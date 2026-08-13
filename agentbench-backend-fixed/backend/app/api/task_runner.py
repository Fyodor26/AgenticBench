"""
Task Runner API Endpoints - Run benchmarks and generate reports
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import logging

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.services.task_runner_service import TaskRunnerService, BenchmarkConfig, ExecutionMode
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/task-runner", tags=["task-runner"])


class TaskRunRequest(BaseModel):
    """Body schema for POST /task-runner/run.

    Previously task_id/mode/agent_ids/etc. were declared as bare function
    parameters, which FastAPI treats as query parameters for primitive
    types. That made this the only POST endpoint in the API that expected
    its arguments in the URL instead of the JSON body. This model fixes
    that inconsistency.
    """
    task_id: int
    mode: ExecutionMode = ExecutionMode.PARALLEL
    agent_ids: Optional[List[int]] = None
    max_concurrent: int = Field(default=5, ge=1, le=50)
    timeout: int = Field(default=60, ge=10, le=600)


async def run_task_benchmark_background(task_id: int, config: BenchmarkConfig):
    from app.db.base import SessionLocal
    from app.services.task_runner_service import TaskRunnerService
    db = SessionLocal()
    try:
        await TaskRunnerService.run_task(db, task_id, config)
    finally:
        db.close()


@router.post("/run")
async def run_task_benchmark(
    request: TaskRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a benchmark for a task against agents"""
    
    task = TaskService.get_task(db, request.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    config = BenchmarkConfig(
        task_id=request.task_id,
        agent_ids=request.agent_ids,
        mode=request.mode,
        max_concurrent=request.max_concurrent,
        timeout_per_eval=request.timeout,
        auto_calculate_metrics=True,
        create_report=True
    )
    
    # Run in background
    background_tasks.add_task(
        run_task_benchmark_background,
        request.task_id,
        config
    )
    
    logger.info(
        f"Started benchmark for task {request.task_id} in {request.mode} mode "
        f"with {len(request.agent_ids or [])} specific agents"
    )
    
    return {
        "message": f"Benchmark started for task '{task.title}'",
        "task_id": request.task_id,
        "mode": request.mode,
        "max_concurrent": request.max_concurrent,
        "timeout_per_agent": request.timeout
    }


@router.get("/results/{task_id}")
def get_task_results(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Get aggregated results for a task"""
    
    try:
        results = TaskRunnerService.get_task_results(db, task_id)
        return results
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting task results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/comparison/{task_id}")
def get_task_comparison(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed agent comparison for a task"""
    
    try:
        comparison = TaskRunnerService.get_task_comparison(db, task_id)
        return comparison
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting comparison: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/tasks/{task_id}/stats")
def get_task_evaluation_stats(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Get evaluation statistics for a task"""
    
    from app.models.task import Task
    from app.models.evaluation import Evaluation, EvaluationMetrics
    from sqlalchemy import func
    
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Get evaluation stats
        total_evals = db.query(func.count(Evaluation.id)).filter(
            Evaluation.task_id == task_id
        ).scalar() or 0
        
        completed_evals = db.query(func.count(Evaluation.id)).filter(
            Evaluation.task_id == task_id,
            Evaluation.status == "completed"
        ).scalar() or 0
        
        failed_evals = db.query(func.count(Evaluation.id)).filter(
            Evaluation.task_id == task_id,
            Evaluation.status == "failed"
        ).scalar() or 0
        
        # Get metrics
        avg_score = db.query(func.avg(EvaluationMetrics.overall_score)).join(
            Evaluation,
            Evaluation.id == EvaluationMetrics.evaluation_id
        ).filter(
            Evaluation.task_id == task_id
        ).scalar() or 0
        
        total_cost = db.query(func.sum(Evaluation.cost)).filter(
            Evaluation.task_id == task_id
        ).scalar() or 0
        
        total_tokens = db.query(func.sum(Evaluation.tokens_used)).filter(
            Evaluation.task_id == task_id
        ).scalar() or 0
        
        return {
            "task_id": task_id,
            "task_title": task.title,
            "total_evaluations": total_evals,
            "completed_evaluations": completed_evals,
            "failed_evaluations": failed_evals,
            "pending_evaluations": total_evals - completed_evals - failed_evals,
            "success_rate": (completed_evals / total_evals * 100) if total_evals > 0 else 0,
            "average_score": round(avg_score, 2),
            "total_cost": round(total_cost, 6),
            "total_tokens": total_tokens
        }
    
    except Exception as e:
        logger.error(f"Error getting task stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/run-all")
async def run_all_tasks(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run benchmarks for all active tasks"""
    
    from app.models.task import Task
    
    active_tasks = db.query(Task).filter(Task.is_active == True).all()
    
    if not active_tasks:
        raise HTTPException(status_code=404, detail="No active tasks found")
    
    logger.info(f"Starting benchmarks for {len(active_tasks)} active tasks")
    
    # Run all tasks in background
    for task in active_tasks:
        config = BenchmarkConfig(task_id=task.id)
        background_tasks.add_task(run_task_benchmark_background, task.id, config)
    
    return {
        "message": f"Started benchmarks for {len(active_tasks)} active tasks",
        "tasks": [{"id": t.id, "title": t.title} for t in active_tasks]
    }


@router.post("/tasks/{task_id}/run-against-agent")
async def run_task_against_agent(
    task_id: int,
    agent_id: int,
    background_tasks: BackgroundTasks,
    timeout: int = Query(60, ge=10, le=600),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a specific task against a specific agent"""
    
    from app.models.task import Task
    from app.models.agent import Agent
    
    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    if not agent.is_active:
        raise HTTPException(status_code=400, detail="Agent is not active")
    
    config = BenchmarkConfig(
        task_id=task_id,
        agent_ids=[agent_id],
        mode="specific_agents",
        timeout_per_eval=timeout
    )
    
    background_tasks.add_task(run_task_benchmark_background, task_id, config)
    
    logger.info(f"Running task {task_id} against agent {agent_id}")
    
    return {
        "message": f"Running task '{task.title}' against agent '{agent.name}'",
        "task_id": task_id,
        "agent_id": agent_id,
        "timeout": timeout
    }


@router.get("/performance-matrix")
def get_performance_matrix(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get performance matrix: agents vs tasks"""
    
    from app.models.task import Task
    from app.models.agent import Agent
    from app.models.evaluation import Evaluation, EvaluationMetrics
    from sqlalchemy import func
    
    try:
        # Get top tasks by evaluation count
        tasks = db.query(
            Task.id,
            Task.title,
            func.count(Evaluation.id).label("eval_count")
        ).outerjoin(
            Evaluation,
            Evaluation.task_id == Task.id
        ).group_by(
            Task.id
        ).order_by(
            func.count(Evaluation.id).desc()
        ).limit(limit).all()
        
        # Get agents
        agents = db.query(Agent).filter(Agent.is_active == True).all()
        
        # Build matrix: agent performance on each task
        matrix = []
        for agent in agents:
            agent_row = {
                "agent_id": agent.id,
                "agent_name": agent.name,
                "provider": agent.provider,
                "tasks": {}
            }
            
            for task_id, task_title, _ in tasks:
                # Get average score for this agent on this task
                avg_score = db.query(func.avg(EvaluationMetrics.overall_score)).join(
                    Evaluation,
                    Evaluation.id == EvaluationMetrics.evaluation_id
                ).filter(
                    Evaluation.agent_id == agent.id,
                    Evaluation.task_id == task_id
                ).scalar() or None
                
                agent_row["tasks"][task_title] = round(avg_score, 2) if avg_score else None
            
            matrix.append(agent_row)
        
        return {
            "tasks": [{"id": t[0], "title": t[1]} for t in tasks],
            "agents": matrix
        }
    
    except Exception as e:
        logger.error(f"Error getting performance matrix: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
