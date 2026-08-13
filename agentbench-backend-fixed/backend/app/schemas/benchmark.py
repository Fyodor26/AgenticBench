from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class BenchmarkCreate(BaseModel):
    title: str
    description: str
    task: str


class BenchmarkUpdate(BaseModel):
    title: str
    description: str
    task: str


class BenchmarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    task: str
    created_by: int
    created_at: Optional[datetime] = None


class BenchmarkRunRequest(BaseModel):
    task_name: str
    prompt: str
    expected_output: Optional[str] = None
    providers: List[str]


class BenchmarkResult(BaseModel):
    provider: str
    # None when no active agent was configured for this provider.
    model: Optional[str] = None
    score: float = 0
    latency: float = 0
    tokens: int = 0
    cost: float = 0
    output: str = ""
    success: bool = False
    error: Optional[str] = None


class BenchmarkRunResponse(BaseModel):
    benchmark_id: int
    status: str
    results: List[BenchmarkResult]
