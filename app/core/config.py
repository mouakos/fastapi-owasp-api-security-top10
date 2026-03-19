"""Configuration settings for the FastAPI app."""

from pydantic import AnyHttpUrl, EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "sqlite+aiosqlite:///./test.db"

    environment: str = "development"
    api_v1_str: str = "/api/v1"
    allowed_origins: str = "http://localhost:3000,http://localhost:8080"

    secret_key: SecretStr = SecretStr("supersecretkey")
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    jwt_issuer: str = "fastapi-owasp-app"
    jwt_audience: str = "fastapi-owasp-api"

    log_level: str = "INFO"
    log_to_file: bool = False
    log_serialized: bool = False

    first_admin_email: EmailStr = "admin@example.com"
    first_admin_username: str = "admin"
    first_admin_password: SecretStr = SecretStr("admin")

    max_failed_login_attempts: int = 5
    lockout_duration_minutes: int = 5

    @property
    def allowed_origins_list(self) -> list[AnyHttpUrl]:
        """Return the allowed origins as a list of URLs."""
        return [AnyHttpUrl(origin.strip()) for origin in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


settings = Settings()
