from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Float, Integer, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Evaluation(Base):
    __tablename__ = "evaluations"
    
    # Composite index for leaderboard queries
    __table_args__ = (
        Index('ix_eval_agent_created', 'agent_id', 'created_at'),
        Index('ix_eval_task_status', 'task_id', 'status'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), index=True)
    agent_id: Mapped[int] = mapped_column(ForeignKey("agents.id"), index=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True)  # pending, running, completed, failed
    agent_response: Mapped[str] = mapped_column(Text, nullable=True)
    execution_time: Mapped[float] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=True)
    cost: Mapped[float] = mapped_column(Float, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    # Track retry attempts
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    # Additional metadata (e.g., stop_reason, model_used, etc.)
    evaluation_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


class EvaluationMetrics(Base):
    __tablename__ = "evaluation_metrics"
    
    # Index for leaderboard aggregation queries
    __table_args__ = (
        Index('ix_metrics_score', 'overall_score'),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[int] = mapped_column(ForeignKey("evaluations.id"), index=True, unique=True)
    correctness_score: Mapped[float] = mapped_column(Float)  # 0-100
    hallucination_score: Mapped[float] = mapped_column(Float)  # 0-100 (higher = fewer hallucinations)
    tool_usage_score: Mapped[float] = mapped_column(Float)  # 0-100 (efficiency of tool use)
    planning_quality_score: Mapped[float] = mapped_column(Float)  # 0-100 (quality of planning)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    success: Mapped[bool] = mapped_column(default=False)
    overall_score: Mapped[float] = mapped_column(Float)  # weighted average
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    execution_time: Mapped[float] = mapped_column(Float, nullable=True)
    tokens_used: Mapped[int] = mapped_column(Integer, nullable=True)
    evaluation_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
