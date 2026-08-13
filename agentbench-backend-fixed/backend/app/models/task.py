from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text)
    prompt: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), index=True)
    difficulty: Mapped[str] = mapped_column(String(50), default="medium")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
