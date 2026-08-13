"""
Evaluations API endpoints
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.evaluation import (
    EvaluationCreate,
    EvaluationResponse,
    EvaluationDetailResponse,
    EvaluationMetricsResponse,
)
from app.services.evaluation_service import EvaluationService
from app.services.executor_service import ExecutorService
from app.services.task_service import TaskService
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


async def run_evaluation_background(evaluation_id: int, prompt: str, expected_output: str, agent_id: int):
    logger.info("Running evaluation %s in background for agent %s", evaluation_id, agent_id)
    from app.db.base import SessionLocal
    db = SessionLocal()
    try:
        agent = AgentService.get_agent(db, agent_id)
        if agent:
            await ExecutorService.execute_evaluation(
                db=db,
                evaluation_id=evaluation_id,
                task_prompt=prompt,
                task_expected_output=expected_output,
                agent=agent,
                timeout=agent.timeout if hasattr(agent, 'timeout') else 60
            )
    finally:
        db.close()


async def run_task_all_agents_background(task_id: int, prompt: str, expected_output: str, agent_ids: list):
    from app.db.base import SessionLocal
    from app.services.executor_service import BatchExecutor
    db = SessionLocal()
    try:
        await BatchExecutor.execute_task_all_agents(
            db=db,
            task_id=task_id,
            task_prompt=prompt,
            task_expected_output=expected_output,
            agent_ids=agent_ids
        )
    finally:
        db.close()


@router.post("/", response_model=EvaluationResponse)
async def create_evaluation(
    eval_data: EvaluationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create and run a new evaluation. Requires auth - this triggers a real,
    potentially billable call to an LLM provider."""

    task = TaskService.get_task(db, eval_data.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    agent = AgentService.get_agent(db, eval_data.agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if not agent.is_active:
        raise HTTPException(status_code=400, detail="Agent is not active")

    evaluation = EvaluationService.create_evaluation(db, eval_data)

    background_tasks.add_task(
        run_evaluation_background,
        evaluation.id,
        task.prompt,
        task.expected_output,
        agent.id
    )

    logger.info(f"Created evaluation {evaluation.id} for task {task.id}, agent {agent.id}")

    return evaluation


@router.get("/{eval_id}", response_model=EvaluationDetailResponse)
def get_evaluation(
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific evaluation with metrics"""

    evaluation = EvaluationService.get_evaluation(db, eval_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    from app.models.evaluation import EvaluationMetrics
    metrics = db.query(EvaluationMetrics).filter(
        EvaluationMetrics.evaluation_id == eval_id
    ).first()

    response = EvaluationResponse.model_validate(evaluation)
    metrics_response = (
        EvaluationMetricsResponse.model_validate(metrics) if metrics else None
    )
    return EvaluationDetailResponse(**response.model_dump(), metrics=metrics_response)


@router.get("/", response_model=list[EvaluationResponse])
def list_evaluations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    task_id: int = Query(None),
    agent_id: int = Query(None),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List evaluations, optionally filtered by task, agent, or status"""

    if task_id:
        evaluations = EvaluationService.get_evaluations_for_task(db, task_id, skip, limit)
    elif agent_id:
        evaluations = EvaluationService.get_evaluations_for_agent(db, agent_id, skip, limit)
    else:
        from app.models.evaluation import Evaluation
        query = db.query(Evaluation)
        if status:
            query = query.filter(Evaluation.status == status)
        evaluations = query.order_by(Evaluation.created_at.desc()).offset(skip).limit(limit).all()

    return evaluations


@router.post("/{eval_id}/calculate-metrics")
async def calculate_metrics(
    eval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate metrics for a completed evaluation"""

    evaluation = EvaluationService.get_evaluation(db, eval_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    if evaluation.status != "completed" or not evaluation.agent_response:
        raise HTTPException(
            status_code=400,
            detail="Evaluation not completed or no response"
        )

    task = TaskService.get_task(db, evaluation.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Associated task not found")

    try:
        metrics = await EvaluationService.calculate_metrics(
            db,
            eval_id,
            task.expected_output,
            evaluation.agent_response,
            execution_time=evaluation.execution_time or 0,
            tokens_used=evaluation.tokens_used,
            cost=evaluation.cost or 0,
            metadata=evaluation.evaluation_metadata
        )
        return metrics
    except Exception as e:
        logger.error(f"Error calculating metrics for evaluation {eval_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating metrics: {str(e)}")


@router.get("/leaderboard/agents")
def get_agent_leaderboard(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get agent leaderboard by average score"""

    try:
        results = EvaluationService.get_agent_leaderboard(db, limit, offset)

        for rank, agent in enumerate(results, 1):
            agent["rank"] = rank + offset

        return results
    except Exception as e:
        logger.error(f"Error getting leaderboard: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting leaderboard: {str(e)}")


@router.post("/{task_id}/run-all-agents")
async def run_task_all_agents(
    task_id: int,
    background_tasks: BackgroundTasks,
    agent_ids: list[int] | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a task against all active agents (or specific agents if provided).
    Requires auth - fans out to potentially many billable LLM calls."""

    task = TaskService.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    background_tasks.add_task(
        run_task_all_agents_background,
        task_id,
        task.prompt,
        task.expected_output,
        agent_ids
    )

    return {
        "message": f"Started evaluation run for task {task_id}",
        "task_id": task_id,
        "agent_ids": agent_ids
    }


@router.get("/stats/overview")
def get_evaluation_stats(db: Session = Depends(get_db)):
    """Get overview statistics about evaluations"""

    try:
        from app.models.evaluation import Evaluation, EvaluationMetrics
        from sqlalchemy import func

        total_evaluations = db.query(func.count(Evaluation.id)).scalar() or 0

        completed = db.query(func.count(Evaluation.id)).filter(
            Evaluation.status == "completed"
        ).scalar() or 0

        failed = db.query(func.count(Evaluation.id)).filter(
            Evaluation.status == "failed"
        ).scalar() or 0

        avg_score = db.query(func.avg(EvaluationMetrics.overall_score)).scalar() or 0

        total_cost = db.query(func.sum(EvaluationMetrics.cost)).scalar() or 0

        successful = db.query(func.count(EvaluationMetrics.id)).filter(
            EvaluationMetrics.success == True  # noqa: E712
        ).scalar() or 0

        success_rate = (successful / completed * 100) if completed > 0 else 0

        return {
            "total_evaluations": total_evaluations,
            "completed_evaluations": completed,
            "failed_evaluations": failed,
            "pending_evaluations": total_evaluations - completed - failed,
            "average_score": round(avg_score, 2),
            "total_cost": round(total_cost, 4),
            "success_rate": round(success_rate, 1),
            "successful_count": successful
        }
    except Exception as e:
        logger.error(f"Error getting evaluation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
