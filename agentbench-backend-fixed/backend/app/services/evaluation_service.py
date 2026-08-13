"""
Enhanced Evaluation Service with advanced metrics calculation
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, Integer, desc

from app.models.evaluation import Evaluation, EvaluationMetrics
from app.models.agent import Agent
from app.schemas.evaluation import EvaluationCreate

logger = logging.getLogger(__name__)


class EvaluationService:
    """Service for evaluation management and metrics calculation"""
    
    @staticmethod
    def create_evaluation(db: Session, eval_data: EvaluationCreate) -> Evaluation:
        """Create a new evaluation record"""
        evaluation = Evaluation(
            task_id=eval_data.task_id,
            agent_id=eval_data.agent_id,
            status="pending",
            evaluation_metadata={}
        )
        db.add(evaluation)
        db.commit()
        db.refresh(evaluation)
        return evaluation

    @staticmethod
    def get_evaluation(db: Session, eval_id: int) -> Evaluation:
        """Get evaluation by ID"""
        return db.query(Evaluation).filter(Evaluation.id == eval_id).first()

    @staticmethod
    def get_evaluations_for_task(db: Session, task_id: int, skip: int = 0, limit: int = 100):
        """Get evaluations for a task"""
        return db.query(Evaluation).filter(
            Evaluation.task_id == task_id
        ).order_by(desc(Evaluation.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    def get_evaluations_for_agent(db: Session, agent_id: int, skip: int = 0, limit: int = 100):
        """Get evaluations for an agent"""
        return db.query(Evaluation).filter(
            Evaluation.agent_id == agent_id
        ).order_by(desc(Evaluation.created_at)).offset(skip).limit(limit).all()

    @staticmethod
    async def calculate_metrics(
        db: Session,
        evaluation_id: int,
        expected_output: str,
        agent_response: str,
        execution_time: float = 0.0,
        tokens_used: Optional[int] = None,
        cost: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EvaluationMetrics:
        """
        Calculate comprehensive metrics for an evaluation
        
        Metrics calculated:
        - Correctness (40%): Semantic similarity to expected output
        - Hallucination (20%): Absence of false/uncertain information
        - Tool Usage (20%): Efficiency of tool and API usage
        - Planning Quality (20%): Quality of reasoning and planning
        """
        
        evaluation = db.query(Evaluation).filter(
            Evaluation.id == evaluation_id
        ).first()
        
        if not evaluation:
            logger.error(f"Evaluation {evaluation_id} not found")
            raise ValueError(f"Evaluation {evaluation_id} not found")
        
        # Calculate individual metrics
        correctness = EvaluationService._calculate_correctness(agent_response, expected_output)
        hallucination = EvaluationService._calculate_hallucination(agent_response)
        tool_usage = EvaluationService._calculate_tool_usage(agent_response)
        planning_quality = EvaluationService._calculate_planning_quality(agent_response)
        
        # Weighted overall score
        overall_score = (
            correctness * 0.4 +
            hallucination * 0.2 +
            tool_usage * 0.2 +
            planning_quality * 0.2
        )
        
        # Create metrics record
        metrics = EvaluationMetrics(
            evaluation_id=evaluation_id,
            correctness_score=correctness,
            hallucination_score=hallucination,
            tool_usage_score=tool_usage,
            planning_quality_score=planning_quality,
            retry_count=evaluation.retry_count,
            success=correctness >= 60,  # 60% correctness = success
            overall_score=overall_score,
            cost=cost,
            execution_time=execution_time,
            tokens_used=tokens_used,
            evaluation_metadata=metadata or {}
        )
        
        db.add(metrics)
        db.commit()
        db.refresh(metrics)
        
        logger.info(
            f"Metrics calculated for evaluation {evaluation_id}: "
            f"overall={overall_score:.1f}, "
            f"correctness={correctness:.1f}, "
            f"hallucination={hallucination:.1f}"
        )
        
        return metrics

    @staticmethod
    def _calculate_correctness(response: str, expected: str) -> float:
        """
        Calculate correctness using multiple similarity metrics
        
        - Jaccard similarity: intersection/union of words
        - Key phrase matching
        - Length similarity
        """
        if not response or not expected:
            return 0.0
        
        response_lower = response.lower()
        expected_lower = expected.lower()
        
        # Exact match
        if response_lower == expected_lower:
            return 100.0
        
        # Word-level similarity (Jaccard)
        response_words = set(response_lower.split())
        expected_words = set(expected_lower.split())
        
        if not expected_words:
            return 0.0
        
        intersection = len(response_words & expected_words)
        union = len(response_words | expected_words)
        
        jaccard = (intersection / union) if union > 0 else 0.0
        
        # Check for key phrases (longer n-grams)
        def extract_phrases(text: str, n: int = 3) -> set:
            words = text.split()
            return {' '.join(words[i:i+n]) for i in range(len(words)-n+1) if len(words[i:i+n]) == n}
        
        response_phrases = extract_phrases(response_lower)
        expected_phrases = extract_phrases(expected_lower)
        
        phrase_match = 0
        if expected_phrases:
            phrase_match = len(response_phrases & expected_phrases) / len(expected_phrases)
        
        # Length penalty (very different lengths are suspicious)
        response_len = len(response_lower)
        expected_len = len(expected_lower)
        length_ratio = min(response_len, expected_len) / max(response_len, expected_len) if max(response_len, expected_len) > 0 else 1.0
        
        # Combined score
        score = (
            jaccard * 0.5 +
            phrase_match * 0.3 +
            length_ratio * 0.2
        ) * 100
        
        return min(100.0, max(0.0, score))

    @staticmethod
    def _calculate_hallucination(response: str) -> float:
        """
        Calculate hallucination score (higher = fewer hallucinations)
        
        Penalize:
        - Uncertainty markers
        - Vague language
        - Unconfirmed claims
        """
        if not response:
            return 100.0
        
        response_lower = response.lower()
        
        # Negative indicators (reduce score)
        uncertainty_patterns = [
            ("i'm not sure", 10),
            ("i don't know", 10),
            ("unclear", 8),
            ("ambiguous", 8),
            ("i think", 5),
            ("i believe", 5),
            ("possibly", 5),
            ("might", 5),
            ("could be", 5),
            ("arguably", 3),
        ]
        
        penalty = 0
        for pattern, weight in uncertainty_patterns:
            if pattern in response_lower:
                penalty += weight
        
        # Positive indicators (boost score)
        confidence_patterns = [
            ("definitely", 5),
            ("certainly", 5),
            ("proven", 5),
            ("verified", 5),
        ]
        
        boost = 0
        for pattern, weight in confidence_patterns:
            if pattern in response_lower:
                boost += weight
        
        score = 100 - penalty + boost
        return min(100.0, max(0.0, score))

    @staticmethod
    def _calculate_tool_usage(response: str) -> float:
        """
        Calculate tool usage efficiency
        
        Positive indicators:
        - API calls
        - Database queries
        - Structured data processing
        """
        if not response:
            return 50.0
        
        response_lower = response.lower()
        
        # Tool usage indicators
        tool_indicators = [
            ("function", 15),
            ("api", 15),
            ("database", 12),
            ("query", 10),
            ("search", 8),
            ("calculate", 8),
            ("retrieve", 8),
            ("fetch", 8),
            ("method", 5),
            ("tool", 5),
            ("request", 5),
        ]
        
        score = 40  # Base score
        for indicator, weight in tool_indicators:
            if indicator in response_lower:
                score += weight
        
        # Penalty for code without execution
        if ("def " in response_lower or "function" in response_lower) and "error" in response_lower:
            score -= 10
        
        return min(100.0, max(0.0, score))

    @staticmethod
    def _calculate_planning_quality(response: str) -> float:
        """
        Calculate planning and reasoning quality
        
        Positive indicators:
        - Structured approach
        - Step-by-step reasoning
        - Clear decision logic
        """
        if not response:
            return 0.0
        
        response_lower = response.lower()
        
        # Planning indicators
        planning_indicators = [
            ("plan", 10),
            ("step", 10),
            ("approach", 10),
            ("strategy", 8),
            ("first", 8),
            ("then", 8),
            ("next", 8),
            ("finally", 8),
            ("thus", 6),
            ("therefore", 6),
            ("consequently", 6),
            ("as a result", 6),
            ("reasoning", 10),
            ("because", 5),
            ("based on", 5),
        ]
        
        score = 0
        for indicator, weight in planning_indicators:
            if indicator in response_lower:
                score += weight
        
        # Bonus for structured formatting
        if "\n" in response or "1." in response or "-" in response:
            score += 10
        
        return min(100.0, max(0.0, score))

    @staticmethod
    def get_agent_leaderboard(
        db: Session,
        limit: int = 50,
        offset: int = 0,
        category: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> list:
        """
        Get agent leaderboard with comprehensive stats
        
        Returns:
            List of dicts with agent info and stats
        """
        
        query = db.query(
            Agent.id,
            Agent.name,
            Agent.provider,
            Agent.model,
            func.avg(EvaluationMetrics.overall_score).label("avg_score"),
            func.count(EvaluationMetrics.id).label("evaluation_count"),
            func.sum(EvaluationMetrics.cost).label("total_cost"),
            func.avg(EvaluationMetrics.execution_time).label("avg_execution_time"),
            func.sum(func.cast(EvaluationMetrics.success, Integer)).label("successful_count"),
        ).join(
            Evaluation,
            Evaluation.agent_id == Agent.id
        ).join(
            EvaluationMetrics,
            EvaluationMetrics.evaluation_id == Evaluation.id
        ).filter(
            Agent.is_active == True
        ).group_by(
            Agent.id
        ).order_by(
            desc("avg_score")
        ).offset(offset).limit(limit)
        
        results = []
        for row in query.all():
            successful = row.successful_count or 0

            success_rate = (
                successful / row.evaluation_count * 100
            ) if row.evaluation_count else 0
            results.append({
                "agent_id": row.id,
                "agent_name": row.name,
                "provider": row.provider,
                "model": row.model,
                "average_score": round(row.avg_score or 0, 2),
                "evaluation_count": row.evaluation_count or 0,
                "total_cost": round(row.total_cost or 0, 4),
                "average_execution_time": round(row.avg_execution_time or 0, 2),
                "success_rate": round(success_rate, 1),
                "successful_evaluations": row.successful_count or 0,
            })
        
        return results
