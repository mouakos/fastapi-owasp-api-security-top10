"""Configuration settings for the FastAPI app."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./test.db"
    database_echo: bool = False

    # General settings
    environment: str = "development"
    version: str = "1.0.0"
    allowed_origins: str = "http://localhost,http://localhost:3000"

    # Security settings
    secret_key: str = "your-secret-key"
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    jwt_issuer: str = "fastapi-owasp-app"
    jwt_audience: str = "fastapi-owasp-api"

    # Logging settings
    log_level: str = "INFO"
    log_to_file: bool = False
    log_serialized: bool = False

    # Account lockout settings
    lockout_minutes: int = 15
    max_failed_attempts: int = 5

    @property
    def allowed_origins_list(self) -> list[str]:
        """Return the allowed origins as a list of strings."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )


settings = Settings()
