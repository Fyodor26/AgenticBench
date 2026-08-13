"""
Application configuration.

Settings are loaded from environment variables / a local .env file (see
.env.example). Nothing in this file should ever contain a real secret -
real secrets belong in the environment or a secrets manager, never in
source control.
"""
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Database ---------------------------------------------------
    DATABASE_URL: str

    # --- Auth ---------------------------------------------------------
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Symmetric key used to encrypt agent/provider credentials before they
    # are persisted (Fernet key - generate with
    # `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`).
    # Falls back to deriving one from SECRET_KEY in development ONLY so the
    # app remains runnable out of the box; production must set this
    # explicitly.
    CREDENTIAL_ENCRYPTION_KEY: Optional[str] = None

    # --- Provider keys (optional - only needed if that provider is used) --
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # --- App / environment ---------------------------------------------
    ENVIRONMENT: str = "development"

    # Comma-separated list in the environment, e.g.
    # CORS_ORIGINS=http://localhost:5173,https://app.example.com
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Auto-create tables on startup. Should be OFF in staging/production -
    # schema changes must go through Alembic migrations there.
    AUTO_CREATE_TABLES: bool = True

    # SQL echo - never enable in production, it leaks query data (including
    # bound parameters) into logs.
    DB_ECHO: bool = False

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_must_be_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in ("production", "prod")


settings = Settings()
