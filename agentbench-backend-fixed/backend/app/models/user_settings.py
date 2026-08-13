from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class UserSettings(Base):
    """Per-user provider configuration and benchmark defaults.

    Provider API keys are stored encrypted (see app.core.security
    encrypt_secret/decrypt_secret) - never in plaintext.
    """

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)

    ollama_base_url: Mapped[str] = mapped_column(String(500), default="http://localhost:11434")

    # Encrypted at rest. Nullable because a user may not configure every provider.
    gemini_api_key_encrypted: Mapped[str] = mapped_column(String(1000), nullable=True)
    openai_api_key_encrypted: Mapped[str] = mapped_column(String(1000), nullable=True)

    judge_model: Mapped[str] = mapped_column(String(50), default="gemini")
    temperature: Mapped[float] = mapped_column(Float, default=0.2)
    max_tokens: Mapped[int] = mapped_column(Integer, default=2048)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
