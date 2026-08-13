"""
Executor Service - Orchestrates agent execution and tracks evaluation lifecycle
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.core.security import decrypt_secret
from app.db.base import SessionLocal
from app.models.agent import Agent
from app.models.evaluation import Evaluation, EvaluationMetrics
from app.agents.executor import AgentExecutor, ExecutionResult
from app.services.evaluation_service import EvaluationService

logger = logging.getLogger(__name__)


class ExecutorService:
    """Service to orchestrate agent execution"""

    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 2
    RETRY_BACKOFF_MULTIPLIER = 2

    @staticmethod
    async def execute_evaluation(
        db: Session,
        evaluation_id: int,
        task_prompt: str,
        task_expected_output: str,
        agent: Agent,
        timeout: int = 60,
        retry: int = 0
    ) -> bool:
        """
        Execute an evaluation - run agent against task and track metrics.

        NOTE: this method commits against the `db` session it's given. When
        called concurrently (see BatchExecutor / TaskRunnerService), each
        concurrent call MUST be given its own dedicated Session - a
        SQLAlchemy Session is not safe to share across concurrently-running
        coroutines/tasks.
        """

        evaluation = db.query(Evaluation).filter(
            Evaluation.id == evaluation_id
        ).first()

        if not evaluation:
            logger.error(f"Evaluation {evaluation_id} not found")
            return False

        try:
            # Set status to running
            evaluation.status = "running"
            evaluation.evaluation_metadata = evaluation.evaluation_metadata or {}
            evaluation.evaluation_metadata["retry_count"] = retry
            db.commit()

            logger.info(f"Starting evaluation {evaluation_id} (retry {retry})")

            # Determine provider and model from agent config
            provider = agent.provider or "generic"
            model = agent.model if hasattr(agent, 'model') else None
            # api_key may already be decrypted plaintext if the caller used
            # AgentService.get_agent_with_decrypted_key; decrypt_secret is a
            # no-op-safe fallback for callers that didn't.
            api_key = decrypt_secret(agent.api_key) if agent.api_key else None

            # Execute the agent.
            # Belt-and-suspenders: even though each executor is expected to
            # enforce `timeout` internally, we wrap the call in an outer
            # asyncio.wait_for as well. If any executor implementation ever
            # forgets to bound its own network call (as OllamaExecutor once
            # did), this still guarantees the evaluation can't hang forever
            # in the "running" state.
            logger.debug("Executing evaluation %s for agent %s", evaluation_id, agent.id)
            try:
                result = await asyncio.wait_for(
                    AgentExecutor.execute(
                        prompt=task_prompt,
                        provider=provider,
                        model=model,
                        api_key=api_key,
                        api_endpoint=agent.api_endpoint if provider == "generic" else None,
                        timeout=timeout,
                        temperature=agent.temperature if hasattr(agent, 'temperature') else 0.7,
                    ),
                    timeout=timeout + 10,
                )
            except asyncio.TimeoutError:
                result = ExecutionResult(
                    success=False,
                    error=f"Evaluation exceeded outer timeout of {timeout + 10}s",
                )
            logger.debug(f"Execution result for evaluation {evaluation_id}: success={result.success}")
            # Record execution results
            evaluation.agent_response = result.output
            evaluation.execution_time = result.execution_time
            evaluation.tokens_used = result.tokens_used
            evaluation.cost = result.cost

            if result.success:
                evaluation.status = "completed"
                evaluation.completed_at = datetime.utcnow()

                # Calculate metrics
                metrics = await EvaluationService.calculate_metrics(
                    db=db,
                    evaluation_id=evaluation_id,
                    expected_output=task_expected_output,
                    agent_response=result.output,
                    execution_time=result.execution_time,
                    tokens_used=result.tokens_used,
                    cost=result.cost,
                    metadata=result.metadata
                )

                logger.info(
                    f"Evaluation {evaluation_id} completed. "
                    f"Score: {metrics.overall_score:.1f}, "
                    f"Cost: ${metrics.cost:.4f}"
                )

            else:
                # Handle failed execution
                evaluation.status = "failed"
                evaluation.error_message = result.error
                evaluation.completed_at = datetime.utcnow()

                logger.error(f"Evaluation {evaluation_id} failed: {result.error}")

                # Retry if within limit
                if retry < ExecutorService.MAX_RETRIES:
                    db.commit()  # Save current state

                    delay = ExecutorService.RETRY_DELAY_SECONDS * (
                        ExecutorService.RETRY_BACKOFF_MULTIPLIER ** retry
                    )
                    logger.info(
                        f"Retrying evaluation {evaluation_id} after {delay}s "
                        f"(attempt {retry + 1}/{ExecutorService.MAX_RETRIES})"
                    )

                    await asyncio.sleep(delay)

                    # Retry
                    return await ExecutorService.execute_evaluation(
                        db=db,
                        evaluation_id=evaluation_id,
                        task_prompt=task_prompt,
                        task_expected_output=task_expected_output,
                        agent=agent,
                        timeout=timeout,
                        retry=retry + 1
                    )

        except Exception as e:
            logger.error(f"Unexpected error executing evaluation {evaluation_id}: {str(e)}")
            evaluation.status = "failed"
            evaluation.error_message = f"Unexpected error: {str(e)}"
            evaluation.completed_at = datetime.utcnow()

        finally:
            # Always commit final state
            db.commit()

        return evaluation.status == "completed"

    @staticmethod
    async def _execute_evaluation_isolated(
        evaluation_id: int,
        task_prompt: str,
        task_expected_output: str,
        agent_id: int,
        timeout: int,
    ) -> bool:
        """
        Run one evaluation on its own dedicated DB session. Use this (rather
        than calling execute_evaluation directly with a shared session) any
        time evaluations are executed concurrently - SQLAlchemy Sessions are
        not safe to use from multiple coroutines/tasks at once.
        """
        session = SessionLocal()
        try:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if not agent:
                logger.error(f"Agent {agent_id} not found for evaluation {evaluation_id}")
                return False
            return await ExecutorService.execute_evaluation(
                db=session,
                evaluation_id=evaluation_id,
                task_prompt=task_prompt,
                task_expected_output=task_expected_output,
                agent=agent,
                timeout=timeout,
            )
        finally:
            session.close()

    @staticmethod
    async def execute_batch_evaluations(
        evaluation_ids: list,
        task_data: dict,
        agent_id: int,
        timeout: int = 60,
        max_concurrent: int = 5
    ) -> dict:
        """
        Execute multiple evaluations concurrently, each on its own DB
        session (see _execute_evaluation_isolated).
        """

        semaphore = asyncio.Semaphore(max_concurrent)

        async def execute_with_limit(eval_id):
            async with semaphore:
                success = await ExecutorService._execute_evaluation_isolated(
                    evaluation_id=eval_id,
                    task_prompt=task_data['prompt'],
                    task_expected_output=task_data['expected_output'],
                    agent_id=agent_id,
                    timeout=timeout,
                )
                return eval_id, success

        tasks = [execute_with_limit(eval_id) for eval_id in evaluation_ids]
        results = await asyncio.gather(*tasks)

        return {eval_id: success for eval_id, success in results}


class BatchExecutor:
    """Executor for running all agents against a task"""

    @staticmethod
    async def execute_task_all_agents(
        db: Session,
        task_id: int,
        task_prompt: str,
        task_expected_output: str,
        agent_ids: Optional[list] = None,
        timeout: int = 60
    ) -> dict:
        """
        Execute a task against specified agents (or all *active* agents if
        not specified). Each agent's evaluation runs on its own DB session
        so this is safe to parallelize later if needed; today it runs them
        sequentially to keep behavior simple and predictable.
        """

        query = db.query(Agent).filter(Agent.is_active == True)  # noqa: E712
        if agent_ids:
            query = query.filter(Agent.id.in_(agent_ids))
        agents = query.all()

        if not agents:
            logger.warning(f"No active agents found for task {task_id}")
            return {}

        logger.info(f"Executing task {task_id} against {len(agents)} agents")

        results = {}

        for agent in agents:
            try:
                # Create evaluation record
                evaluation = Evaluation(
                    task_id=task_id,
                    agent_id=agent.id,
                    status="pending"
                )
                db.add(evaluation)
                db.commit()
                db.refresh(evaluation)

                # Execute
                success = await ExecutorService._execute_evaluation_isolated(
                    evaluation_id=evaluation.id,
                    task_prompt=task_prompt,
                    task_expected_output=task_expected_output,
                    agent_id=agent.id,
                    timeout=timeout
                )

                results[agent.id] = {
                    "evaluation_id": evaluation.id,
                    "success": success,
                    "status": "completed" if success else "failed"
                }

            except Exception as e:
                logger.error(f"Error executing task for agent {agent.id}: {str(e)}")
                results[agent.id] = {
                    "success": False,
                    "error": str(e),
                    "status": "error"
                }

        return results
