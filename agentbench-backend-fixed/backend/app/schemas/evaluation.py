from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class EvaluationMetricsResponse(BaseModel):
    id: int
    evaluation_id: int
    correctness_score: float
    hallucination_score: float
    tool_usage_score: float
    planning_quality_score: float
    retry_count: int
    success: bool
    overall_score: float
    evaluation_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EvaluationCreate(BaseModel):
    task_id: int
    agent_id: int


class EvaluationResponse(BaseModel):
    id: int
    task_id: int
    agent_id: int
    status: str
    agent_response: Optional[str] = None
    execution_time: Optional[float] = None
    tokens_used: Optional[int] = None
    cost: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class EvaluationDetailResponse(EvaluationResponse):
    metrics: Optional[EvaluationMetricsResponse] = None
