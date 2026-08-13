from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str

    provider: str = "ollama"

    model: Optional[str] = None

    api_endpoint: Optional[str] = None

    api_key: Optional[str] = None

    temperature: float = 0.7

    max_tokens: int = 2048

    timeout: int = 60

    is_active: bool = True


class AgentUpdate(BaseModel):

    name: Optional[str] = None

    description: Optional[str] = None

    provider: Optional[str] = None

    model: Optional[str] = None

    api_endpoint: Optional[str] = None

    api_key: Optional[str] = None

    temperature: Optional[float] = None

    max_tokens: Optional[int] = None

    timeout: Optional[int] = None

    is_active: Optional[bool] = None


class AgentResponse(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id: int

    name: str

    description: str

    provider: str

    model: Optional[str]

    api_endpoint: Optional[str]

    temperature: float

    max_tokens: int

    timeout: int

    is_active: bool

    created_at: datetime

    updated_at: datetime