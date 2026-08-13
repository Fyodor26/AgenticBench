from datetime import datetime
from sqlalchemy import String, Text, DateTime, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    # Provider type: "openai", "anthropic", "generic", "mock"
    provider: Mapped[str] = mapped_column(String(50), default="generic", index=True)
    # Model name (for OpenAI/Anthropic)
    model: Mapped[str] = mapped_column(String(255), nullable=True)
    # For generic/custom agents
    api_endpoint: Mapped[str] = mapped_column(String(500), nullable=True)
    # Stored ENCRYPTED at rest (see app.core.security.encrypt_secret/decrypt_secret).
    # Never return this column directly in an API response.
    api_key: Mapped[str] = mapped_column(String(1000), nullable=True)
    # Temperature for LLM sampling
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    # Max tokens
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)
    # Timeout for execution
    timeout: Mapped[int] = mapped_column(Integer, default=60)
    # Is this agent active/enabled
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
