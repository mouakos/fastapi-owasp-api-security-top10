"""Configuration settings for the FastAPI app."""

from pydantic import EmailStr, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "sqlite+aiosqlite:///./test.db"

    environment: str = "development"
    allowed_origins: str = "http://localhost,http://localhost:3000"

    secret_key: SecretStr = SecretStr("supersecretkey")
    access_token_expire_minutes: int = 30

    log_level: str = "INFO"
    log_to_file: bool = False
    log_serialized: bool = False

    first_admin_email: EmailStr = "admin@example.com"
    first_admin_username: str = "admin"
    first_admin_password: SecretStr = SecretStr("admin")

    @property
    def allowed_origins_list(self) -> list[str]:
        """Return the allowed origins as a list of strings."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


settings = Settings()
