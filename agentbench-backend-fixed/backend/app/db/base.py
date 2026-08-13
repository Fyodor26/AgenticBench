"""
Single source of truth for the SQLAlchemy engine, session factory, and
declarative base.

Previously this project had TWO separate places creating an engine and a
sessionmaker (app/db/base.py and app/db/database.py) with different
settings (one had echo=True, i.e. it dumped every SQL statement - including
bound parameters, which can include passwords and API keys - to stdout).
Two engines also means two separate connection pools for the same
database, which wastes connections and can mask session/transaction bugs.

app/db/database.py now just re-exports the names below for backwards
compatibility with existing imports elsewhere in the codebase.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

Base = declarative_base()

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO and not settings.is_production,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)
