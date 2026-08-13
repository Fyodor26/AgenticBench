from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserSettingsUpdate(BaseModel):
    ollama_base_url: Optional[str] = None
    gemini_api_key: Optional[str] = Field(default=None, description="Write-only; never returned")
    openai_api_key: Optional[str] = Field(default=None, description="Write-only; never returned")
    judge_model: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, ge=1, le=32000)


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ollama_base_url: str
    # Booleans only - never echo the actual key back to the client.
    gemini_api_key_set: bool = False
    openai_api_key_set: bool = False
    judge_model: str
    temperature: float
    max_tokens: int
