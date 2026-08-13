"""
Dev-convenience table creation.

This should NOT run in staging/production - schema changes there must go
through Alembic migrations (see /alembic/versions). Running
`Base.metadata.create_all` on every startup alongside a separate Alembic
migration history is a recipe for silent schema drift: if someone edits a
model without writing a migration, create_all will happily patch the dev
DB and hide the fact that the migration is missing until it breaks a real
environment.
"""
import logging

from app.core.config import settings
from app.db.base import Base, engine

# Import all models so they're registered on Base.metadata before create_all
from app.models.user import User  # noqa: F401
from app.models.agent import Agent  # noqa: F401
from app.models.task import Task  # noqa: F401
from app.models.evaluation import Evaluation, EvaluationMetrics  # noqa: F401
from app.models.benchmark import Benchmark  # noqa: F401
from app.models.user_settings import UserSettings  # noqa: F401

logger = logging.getLogger(__name__)


def init_db() -> None:
    if settings.is_production:
        logger.info(
            "ENVIRONMENT=%s: skipping auto table creation, run "
            "'alembic upgrade head' to apply migrations.",
            settings.ENVIRONMENT,
        )
        return

    if not settings.AUTO_CREATE_TABLES:
        logger.info("AUTO_CREATE_TABLES=false: skipping auto table creation.")
        return

    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured (development convenience mode).")
