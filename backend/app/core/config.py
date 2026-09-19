import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(Path(__file__).resolve().parents[3] / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = Field(default="development")
    APP_NAME: str = "Fear-Free Family Truth Companion"
    APP_TAGLINE: str = "Understand your loan. Involve your family. Decide with confidence."
    APP_BASE_URL: str = Field(default="http://localhost:3000")
    API_V1_PREFIX: str = "/api/v1"

    # MongoDB
    MONGODB_URI: str = Field(default="mongodb://localhost:27017")
    MONGODB_DATABASE: str = Field(default="fear_free_companion")

    # Local Ollama LLM
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="qwen2.5:7b")
    OLLAMA_TIMEOUT_SECONDS: int = Field(default=60)
    OLLAMA_NUM_CTX: int = Field(default=8192)

    # External Anthropic-compatible LLM (optional; used before Ollama)
    LLM_API_KEY: str = Field(default="")
    LLM_BASE_URL: str = Field(default="")
    LLM_MODEL: str = Field(default="")
    LLM_TIMEOUT_SECONDS: int = Field(default=90)

    # Cognee knowledge and retrieval service
    COGNEE_API_URL: str = Field(default="https://api.cognee.ai")
    COGNEE_API_KEY: str = Field(default="")
    COGNEE_TENANT_ID: str = Field(default="")
    # n8n WhatsApp workflow
    N8N_WHATSAPP_WEBHOOK_URL: str = Field(default="")

    # File Storage & Limits
    UPLOAD_DIRECTORY: str = Field(default="./data/uploads")
    MAX_UPLOAD_MB: int = Field(default=20)
    MAX_PDF_PAGES: int = Field(default=100)
    DOCUMENT_RETENTION_DAYS: int = Field(default=30)

    # Authentication & Session
    SESSION_TTL_HOURS: int = Field(default=24)
    COOKIE_NAME: str = "ff_session"
    CSRF_COOKIE_NAME: str = "ff_csrf"
    COOKIE_SECURE: bool = Field(default=False)
    COOKIE_SAMESITE: str = Field(default="lax")
    CSRF_SECRET: str = Field(default="dev-secret-key-must-be-at-least-32-chars-long-for-fear-free-truth")

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000"
    ]

    # SMTP Configuration
    SMTP_HOST: str = Field(default="localhost")
    SMTP_PORT: int = Field(default=1025)
    SMTP_FROM: str = Field(default="no-reply@fearfreecompanion.local")
    SMTP_USER: str = Field(default="")
    SMTP_PASSWORD: str = Field(default="")
    SMTP_USE_TLS: bool = Field(default=False)

    # Worker Settings
    WORKER_POLL_INTERVAL_SECONDS: float = Field(default=2.0)
    WORKER_LEASE_SECONDS: int = Field(default=120)
    WORKER_HEARTBEAT_SECONDS: int = Field(default=15)
    WORKER_MAX_RETRIES: int = Field(default=3)

    @field_validator("CSRF_SECRET")
    @classmethod
    def validate_csrf_secret(cls, v: str, info) -> str:
        if len(v) < 32:
            raise ValueError("CSRF_SECRET must be at least 32 characters long for security.")
        return v

    def validate_production_safety(self) -> None:
        """Fail startup if critical security settings are unsafe in production."""
        if self.APP_ENV.lower() == "production":
            if not self.COOKIE_SECURE:
                raise ValueError("COOKIE_SECURE must be True in production environments.")
            if "localhost" in self.APP_BASE_URL:
                raise ValueError("APP_BASE_URL must not use localhost in production.")
            if self.CSRF_SECRET.startswith("dev-secret"):
                raise ValueError("Default development CSRF_SECRET is not permitted in production.")


settings = Settings()
os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
