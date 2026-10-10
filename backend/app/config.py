"""Configuration management for QueryPilot backend."""

from functools import lru_cache
from pathlib import Path
import re
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Locate backend and root directory paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    frontend_origin: str = Field(default="http://localhost:5173", alias="FRONTEND_ORIGIN")

    # Gemini LLM Provider
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    # LangSmith Tracing
    langsmith_api_key: Optional[str] = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_project: str = Field(default="querypilot-dev", alias="LANGSMITH_PROJECT")
    langsmith_endpoint: str = Field(
        default="https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT"
    )

    # Database Configuration
    database_url: str = Field(
        default="postgresql+psycopg2://querypilot_readonly:change_me@localhost:5432/querypilot",
        alias="DATABASE_URL",
    )
    database_dialect: str = Field(default="postgres", alias="DATABASE_DIALECT")
    query_timeout_seconds: int = Field(default=10, alias="QUERY_TIMEOUT_SECONDS")
    max_rows: int = Field(default=500, alias="MAX_ROWS")
    max_sql_repair_attempts: int = Field(default=3, alias="MAX_SQL_REPAIR_ATTEMPTS")

    model_config = SettingsConfigDict(
        env_file=(
            str(BACKEND_DIR / ".env"),
            str(ROOT_DIR / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_gemini_configured(self) -> bool:
        """Check if a valid, non-placeholder Google API key is configured."""
        if not self.google_api_key:
            return False
        cleaned = self.google_api_key.strip()
        return bool(cleaned and cleaned != "your_google_api_key_here")

    @property
    def is_langsmith_configured(self) -> bool:
        """Check if LangSmith tracing is active with valid key."""
        if not self.langsmith_tracing:
            return False
        if not self.langsmith_api_key:
            return False
        cleaned = self.langsmith_api_key.strip()
        return bool(cleaned and cleaned != "your_langsmith_api_key_here")

    @property
    def is_database_configured(self) -> bool:
        """Check if database URL has been customized from default placeholder."""
        if not self.database_url:
            return False
        return "change_me" not in self.database_url

    @property
    def sanitized_database_url(self) -> str:
        """Return database URL with password masked for safe logging or health display."""
        if not self.database_url:
            return ""
        # Mask password in URL scheme: //user:password@host
        return re.sub(r":([^:@/]+)@", r":***@", self.database_url)


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton instance of Settings."""
    return Settings()
