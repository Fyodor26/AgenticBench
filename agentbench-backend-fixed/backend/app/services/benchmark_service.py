import logging

from sqlalchemy.orm import Session

from app.models.benchmark import Benchmark
from app.schemas.benchmark import BenchmarkRunRequest
from app.models.task import Task
from app.models.agent import Agent
from app.models.evaluation import Evaluation, EvaluationMetrics
from app.services.executor_service import ExecutorService

logger = logging.getLogger(__name__)


class BenchmarkService:

    @staticmethod
    def create(db: Session, data, user_id: int):
        benchmark = Benchmark(
            title=data.title,
            description=data.description,
            task=data.task,
            created_by=user_id,
        )
        db.add(benchmark)
        db.commit()
        db.refresh(benchmark)
        return benchmark

    @staticmethod
    def get_all(db: Session, user_id: int):
        """
        List benchmark run history for the Results page.

        `run()` below creates a Task (category="Benchmark") per quick-run,
        not a row in the separate `benchmarks` table - that table backs a
        distinct (currently frontend-unused) "saved benchmark definition"
        CRUD feature (see create/get_by_id). Previously this method read
        from `benchmarks`, so the Results page would always show "No
        benchmark history found" even after successfully running
        benchmarks, because nothing ever wrote a row there. Reading from
        Task history instead makes the Results page reflect what users
        actually ran.
        """
        tasks = (
            db.query(Task)
            .filter(Task.created_by == user_id, Task.category == "Benchmark")
            .order_by(Task.created_at.desc())
            .all()
        )
        return [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "task": task.prompt,
                "created_by": task.created_by,
                "created_at": task.created_at,
            }
            for task in tasks
        ]

    @staticmethod
    def get_by_id(db: Session, benchmark_id: int, user_id: int):
        return (
            db.query(Benchmark)
            .filter(
                Benchmark.id == benchmark_id,
                Benchmark.created_by == user_id,
            )
            .first()
        )

    @staticmethod
    async def run(db: Session, request: BenchmarkRunRequest, user_id: int):
        """
        Run the given prompt/task against every requested provider and
        return one result per provider.

        Previously this only ever looked at `request.providers[0]` - if a
        user selected multiple providers in the "Quick Benchmark" UI, every
        provider after the first was silently ignored. This runs (and
        scores) all of them.
        """
        task = Task(
            title=request.task_name,
            description=request.expected_output or "",
            prompt=request.prompt,
            expected_output=request.expected_output or "",
            category="Benchmark",
            difficulty="medium",
            created_by=user_id,
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        results = []

        for provider in request.providers:
            agent = (
                db.query(Agent)
                .filter(Agent.provider == provider, Agent.is_active == True)  # noqa: E712
                .first()
            )

            if not agent:
                results.append({
                    "provider": provider,
                    "model": None,
                    "score": 0,
                    "latency": 0,
                    "tokens": 0,
                    "cost": 0,
                    "output": "",
                    "success": False,
                    "error": f"No active {provider} agent configured",
                })
                continue

            evaluation = Evaluation(
                task_id=task.id,
                agent_id=agent.id,
                status="pending",
            )
            db.add(evaluation)
            db.commit()
            db.refresh(evaluation)

            await ExecutorService.execute_evaluation(
                db=db,
                evaluation_id=evaluation.id,
                task_prompt=task.prompt,
                task_expected_output=task.expected_output,
                agent=agent,
                timeout=agent.timeout,
            )

            db.refresh(evaluation)
            metrics = (
                db.query(EvaluationMetrics)
                .filter(EvaluationMetrics.evaluation_id == evaluation.id)
                .first()
            )

            results.append({
                "provider": agent.provider,
                "model": agent.model,
                "score": metrics.overall_score if metrics else 0,
                "latency": evaluation.execution_time or 0,
                "tokens": evaluation.tokens_used or 0,
                "cost": evaluation.cost or 0,
                "output": evaluation.agent_response or "",
                "success": evaluation.status == "completed",
            })

        return {
            "benchmark_id": task.id,
            "status": "completed",
            "results": results,
        }

    @staticmethod
    def get_results(db: Session, benchmark_id: int, user_id: int):
        """
        Get results for a benchmark run. Scoped to the requesting user via
        the owning Task's created_by column - previously this looked up an
        evaluation purely by task_id with no ownership check at all, so any
        authenticated user could read any other user's benchmark output
        (IDOR).
        """
        task = (
            db.query(Task)
            .filter(Task.id == benchmark_id, Task.created_by == user_id)
            .first()
        )
        if not task:
            return {"results": []}

        evaluations = (
            db.query(Evaluation)
            .filter(Evaluation.task_id == task.id)
            .all()
        )

        results = []
        for evaluation in evaluations:
            metrics = (
                db.query(EvaluationMetrics)
                .filter(EvaluationMetrics.evaluation_id == evaluation.id)
                .first()
            )
            agent = db.query(Agent).filter(Agent.id == evaluation.agent_id).first()
            if not agent:
                continue

            results.append({
                "provider": agent.provider,
                "model": agent.model,
                "score": metrics.overall_score if metrics else 0,
                "latency": evaluation.execution_time or 0,
                "tokens": evaluation.tokens_used or 0,
                "cost": evaluation.cost or 0,
                "output": evaluation.agent_response or "",
                "success": evaluation.status == "completed",
            })

        return {"results": results}
