"""Configuration classes — SQLite for dev, PostgreSQL for prod."""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class _BaseConfig:
    """Shared configuration across all environments."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-fallback-secret-key")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-jwt-fallback")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM defaults (local-first)
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    LLM_API_KEY: str = os.getenv("LLM_API_KEY", "ollama")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.2")


class DevelopmentConfig(_BaseConfig):
    """Local development — SQLite, debug on."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'nestscout_dev.db'}",
    )


class ProductionConfig(_BaseConfig):
    """Production — PostgreSQL + PostGIS required."""

    DEBUG = False
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "postgresql://localhost/nestscout"
    )


class TestingConfig(_BaseConfig):
    """Test suite — in-memory SQLite."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=5)


config_by_name: dict[str, type[_BaseConfig]] = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
