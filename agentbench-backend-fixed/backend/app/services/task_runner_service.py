"""
Task Runner Service - Executes tasks against agents and generates benchmarks
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.db.base import SessionLocal
from app.models.task import Task
from app.models.agent import Agent
from app.models.evaluation import Evaluation, EvaluationMetrics
from app.services.executor_service import ExecutorService, BatchExecutor

logger = logging.getLogger(__name__)


class ExecutionMode(str, Enum):
    """Execution mode for task running"""
    ALL_AGENTS = "all_agents"          # Run all active agents
    SPECIFIC_AGENTS = "specific_agents"  # Run specific agents
    SEQUENTIAL = "sequential"            # Run one at a time
    PARALLEL = "parallel"               # Run all concurrently


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run"""
    task_id: int
    agent_ids: Optional[List[int]] = None
    mode: ExecutionMode = ExecutionMode.PARALLEL
    max_concurrent: int = 5
    timeout_per_eval: int = 60
    auto_calculate_metrics: bool = True
    create_report: bool = True


@dataclass
class BenchmarkResult:
    """Result from a benchmark run"""
    benchmark_id: str
    task_id: int
    total_agents: int
    completed: int
    failed: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    evaluations: List[Dict[str, Any]]
    summary_stats: Dict[str, Any]


class TaskRunnerService:
    """Service for running tasks against agents"""
    
    @staticmethod
    async def run_task(
        db: Session,
        task_id: int,
        config: BenchmarkConfig
    ) -> BenchmarkResult:
        """
        Run a task against agents with comprehensive benchmarking
        
        Args:
            db: Database session
            task_id: ID of task to run
            config: Benchmark configuration
        
        Returns:
            BenchmarkResult with execution details
        """
        
        # Load task
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        logger.info(f"Starting task runner for task {task_id}: {task.title}")
        
        # Get agents to run
        agents = TaskRunnerService._get_agents_to_run(db, config)
        if not agents:
            raise ValueError("No agents found to run")
        
        logger.info(f"Running against {len(agents)} agents in {config.mode} mode")
        
        start_time = datetime.utcnow()
        
        # Execute based on mode
        if config.mode == ExecutionMode.SEQUENTIAL:
            evaluations = await TaskRunnerService._run_sequential(
                db, task, agents, config
            )
        else:  # PARALLEL
            evaluations = await TaskRunnerService._run_parallel(
                db, task, agents, config
            )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate summary statistics
        summary = TaskRunnerService._calculate_summary(db, evaluations)
        
        result = BenchmarkResult(
            benchmark_id=f"bench_{task_id}_{start_time.timestamp()}",
            task_id=task_id,
            total_agents=len(agents),
            completed=sum(1 for e in evaluations if e.get("success")),
            failed=sum(1 for e in evaluations if not e.get("success")),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            evaluations=evaluations,
            summary_stats=summary
        )
        
        logger.info(
            f"Task {task_id} complete. "
            f"Completed: {result.completed}/{result.total_agents}, "
            f"Duration: {duration:.1f}s"
        )
        
        return result
    
    @staticmethod
    def _get_agents_to_run(
        db: Session,
        config: BenchmarkConfig
    ) -> List[Agent]:
        """Get agents to run based on config"""
        
        query = db.query(Agent).filter(Agent.is_active == True)
        
        if config.agent_ids:
            query = query.filter(Agent.id.in_(config.agent_ids))
        
        agents = query.all()
        return agents
    
    @staticmethod
    async def _run_sequential(
        db: Session,
        task: Task,
        agents: List[Agent],
        config: BenchmarkConfig
    ) -> List[Dict[str, Any]]:
        """Run task against agents sequentially"""
        
        evaluations = []
        
        for agent in agents:
            try:
                evaluation = Evaluation(
                    task_id=task.id,
                    agent_id=agent.id,
                    status="pending"
                )
                db.add(evaluation)
                db.commit()
                db.refresh(evaluation)
                
                # Execute
                success = await ExecutorService.execute_evaluation(
                    db=db,
                    evaluation_id=evaluation.id,
                    task_prompt=task.prompt,
                    task_expected_output=task.expected_output,
                    agent=agent,
                    timeout=config.timeout_per_eval
                )
                
                eval_result = TaskRunnerService._format_evaluation_result(
                    db, evaluation, success
                )
                evaluations.append(eval_result)
                
            except Exception as e:
                logger.error(f"Error executing task for agent {agent.id}: {str(e)}")
                evaluations.append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "success": False,
                    "error": str(e)
                })
        
        return evaluations
    
    @staticmethod
    async def _run_parallel(
        db: Session,
        task: Task,
        agents: List[Agent],
        config: BenchmarkConfig
    ) -> List[Dict[str, Any]]:
        """Run task against agents in parallel.

        Each concurrent evaluation executes on its own dedicated DB session
        (opened/closed inside execute_with_limit) rather than sharing `db`.
        SQLAlchemy's Session is not safe to use from multiple
        coroutines/tasks concurrently - sharing one here previously meant
        parallel runs could corrupt evaluation state or raise obscure
        DBAPI errors under load.
        """

        # Create evaluation records for all agents up front, using the
        # request-scoped session (this part is sequential, so it's safe).
        evaluations_to_run = []
        for agent in agents:
            evaluation = Evaluation(
                task_id=task.id,
                agent_id=agent.id,
                status="pending"
            )
            db.add(evaluation)
            evaluations_to_run.append((evaluation, agent))

        db.commit()
        for evaluation, _ in evaluations_to_run:
            db.refresh(evaluation)

        # Execute in parallel with semaphore, one isolated session per task
        semaphore = asyncio.Semaphore(config.max_concurrent)

        async def execute_with_limit(evaluation_id: int, agent: Agent):
            async with semaphore:
                session = SessionLocal()
                try:
                    try:
                        success = await ExecutorService.execute_evaluation(
                            db=session,
                            evaluation_id=evaluation_id,
                            task_prompt=task.prompt,
                            task_expected_output=task.expected_output,
                            agent=agent,
                            timeout=config.timeout_per_eval
                        )
                        evaluation = session.query(Evaluation).filter(
                            Evaluation.id == evaluation_id
                        ).first()
                        return TaskRunnerService._format_evaluation_result(
                            session, evaluation, success
                        )
                    except Exception as e:
                        logger.error(f"Error executing agent {agent.id}: {str(e)}")
                        return {
                            "agent_id": agent.id,
                            "agent_name": agent.name,
                            "success": False,
                            "error": str(e)
                        }
                finally:
                    session.close()

        tasks = [
            execute_with_limit(evaluation.id, agent)
            for evaluation, agent in evaluations_to_run
        ]

        results = await asyncio.gather(*tasks)
        return results
    
    @staticmethod
    def _format_evaluation_result(
        db: Session,
        evaluation: Evaluation,
        success: bool
    ) -> Dict[str, Any]:
        """Format evaluation result for response"""
        
        # Fetch metrics if available
        metrics = db.query(EvaluationMetrics).filter(
            EvaluationMetrics.evaluation_id == evaluation.id
        ).first()
        
        agent = db.query(Agent).filter(Agent.id == evaluation.agent_id).first()
        
        result = {
            "evaluation_id": evaluation.id,
            "agent_id": evaluation.agent_id,
            "agent_name": agent.name if agent else "Unknown",
            "status": evaluation.status,
            "success": success,
            "execution_time": evaluation.execution_time,
            "tokens_used": evaluation.tokens_used,
            "cost": evaluation.cost,
        }
        
        if metrics:
            result["metrics"] = {
                "overall_score": metrics.overall_score,
                "correctness": metrics.correctness_score,
                "hallucination": metrics.hallucination_score,
                "tool_usage": metrics.tool_usage_score,
                "planning_quality": metrics.planning_quality_score,
                "success": metrics.success,
            }
        
        if evaluation.error_message:
            result["error"] = evaluation.error_message
        
        return result
    
    @staticmethod
    def _calculate_summary(
        db: Session,
        evaluations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate summary statistics from evaluations"""
        
        completed = [e for e in evaluations if e.get("success")]
        failed = [e for e in evaluations if not e.get("success")]
        
        # Score statistics
        scores = [
            e.get("metrics", {}).get("overall_score", 0)
            for e in completed if "metrics" in e
        ]
        
        # Cost statistics
        costs = [e.get("cost", 0) for e in completed]
        
        # Time statistics
        times = [e.get("execution_time", 0) for e in completed if e.get("execution_time")]
        
        return {
            "total_evaluations": len(evaluations),
            "successful_evaluations": len(completed),
            "failed_evaluations": len(failed),
            "success_rate": (len(completed) / len(evaluations) * 100) if evaluations else 0,
            "scores": {
                "mean": sum(scores) / len(scores) if scores else 0,
                "max": max(scores) if scores else 0,
                "min": min(scores) if scores else 0,
                "median": sorted(scores)[len(scores)//2] if scores else 0,
            },
            "costs": {
                "total": sum(costs),
                "mean": sum(costs) / len(costs) if costs else 0,
                "max": max(costs) if costs else 0,
            },
            "execution_time": {
                "mean": sum(times) / len(times) if times else 0,
                "max": max(times) if times else 0,
                "min": min(times) if times else 0,
            }
        }
    
    @staticmethod
    def get_task_results(
        db: Session,
        task_id: int
    ) -> Dict[str, Any]:
        """Get aggregated results for a task"""
        
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Get all evaluations for this task
        evaluations = db.query(Evaluation).filter(
            Evaluation.task_id == task_id,
            Evaluation.status == "completed"
        ).all()
        
        if not evaluations:
            return {
                "task_id": task_id,
                "task_title": task.title,
                "evaluations_count": 0,
                "message": "No completed evaluations for this task"
            }
        
        # Get metrics for all evaluations
        eval_ids = [e.id for e in evaluations]
        metrics_list = db.query(EvaluationMetrics).filter(
            EvaluationMetrics.evaluation_id.in_(eval_ids)
        ).all()
        
        # Agent performance
        agent_performance = {}
        for evaluation in evaluations:
            agent = db.query(Agent).filter(Agent.id == evaluation.agent_id).first()
            metrics = db.query(EvaluationMetrics).filter(
                EvaluationMetrics.evaluation_id == evaluation.id
            ).first()
            
            if agent:
                if agent.id not in agent_performance:
                    agent_performance[agent.id] = {
                        "agent_name": agent.name,
                        "provider": agent.model or agent.provider,
                        "evaluations": 0,
                        "total_cost": 0,
                        "scores": []
                    }
                
                agent_performance[agent.id]["evaluations"] += 1
                agent_performance[agent.id]["total_cost"] += evaluation.cost or 0
                
                if metrics:
                    agent_performance[agent.id]["scores"].append(metrics.overall_score)
        
        # Calculate averages
        for agent_id, perf in agent_performance.items():
            if perf["scores"]:
                perf["average_score"] = sum(perf["scores"]) / len(perf["scores"])
                perf["max_score"] = max(perf["scores"])
                perf["min_score"] = min(perf["scores"])
            perf.pop("scores")  # Don't return all individual scores
        
        return {
            "task_id": task_id,
            "task_title": task.title,
            "task_category": task.category,
            "evaluations_count": len(evaluations),
            "agent_performance": agent_performance,
            "summary": {
                "total_evaluations": len(evaluations),
                "total_cost": sum(e.cost or 0 for e in evaluations),
                "total_tokens": sum(e.tokens_used or 0 for e in evaluations)
            }
        }
    
    @staticmethod
    def get_task_comparison(
        db: Session,
        task_id: int
    ) -> Dict[str, Any]:
        """Get detailed comparison of agents on a task"""
        
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # Get all completed evaluations with metrics
        query = db.query(
            Agent.id,
            Agent.name,
            Agent.provider,
            Agent.model,
            Evaluation.execution_time,
            Evaluation.tokens_used,
            Evaluation.cost,
            EvaluationMetrics.overall_score,
            EvaluationMetrics.correctness_score,
            EvaluationMetrics.hallucination_score,
            EvaluationMetrics.tool_usage_score,
            EvaluationMetrics.planning_quality_score,
            EvaluationMetrics.success,
        ).join(
            Evaluation,
            Evaluation.agent_id == Agent.id
        ).join(
            EvaluationMetrics,
            EvaluationMetrics.evaluation_id == Evaluation.id
        ).filter(
            Evaluation.task_id == task_id,
            Evaluation.status == "completed"
        ).all()
        
        if not query:
            return {
                "task_id": task_id,
                "task_title": task.title,
                "agents_count": 0,
                "message": "No completed evaluations to compare"
            }
        
        # Format results
        agents = []
        for row in query:
            agents.append({
                "agent_id": row[0],
                "agent_name": row[1],
                "provider": row[2],
                "model": row[3],
                "execution_time": round(row[4] or 0, 2),
                "tokens_used": row[5],
                "cost": round(row[6] or 0, 6),
                "overall_score": round(row[7], 2),
                "correctness": round(row[8], 1),
                "hallucination": round(row[9], 1),
                "tool_usage": round(row[10], 1),
                "planning_quality": round(row[11], 1),
                "success": row[12],
            })
        
        # Sort by score
        agents = sorted(agents, key=lambda x: x["overall_score"], reverse=True)
        
        # Add rankings
        for rank, agent in enumerate(agents, 1):
            agent["rank"] = rank
        
        return {
            "task_id": task_id,
            "task_title": task.title,
            "task_category": task.category,
            "agents_count": len(agents),
            "agents": agents
        }


class BenchmarkScheduler:
    """Scheduler for periodic benchmark runs"""
    
    @staticmethod
    async def schedule_task(
        db: Session,
        task_id: int,
        interval_hours: int = 24
    ) -> None:
        """Schedule periodic benchmark runs for a task"""
        
        # TODO: Implement scheduling logic
        # This would integrate with a task scheduler like APScheduler
        
        logger.info(f"Scheduled task {task_id} to run every {interval_hours} hours")
    
    @staticmethod
    async def run_all_active_tasks(db: Session) -> List[BenchmarkResult]:
        """Run benchmarks for all active tasks"""
        
        tasks = db.query(Task).filter(Task.is_active == True).all()
        
        results = []
        for task in tasks:
            try:
                config = BenchmarkConfig(
                    task_id=task.id,
                    mode=ExecutionMode.PARALLEL
                )
                result = await TaskRunnerService.run_task(db, task.id, config)
                results.append(result)
            except Exception as e:
                logger.error(f"Error running task {task.id}: {str(e)}")
        
        return results
