from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Benchmark(Base):

    __tablename__ = "benchmarks"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(200),
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text
    )

    task: Mapped[str] = mapped_column(
        Text
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )