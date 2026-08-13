from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str
    prompt: str
    expected_output: str
    category: str
    difficulty: Optional[str] = "medium"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    expected_output: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str
    prompt: str
    expected_output: str
    category: str
    difficulty: str
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
