"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """AI Habitat application settings.

    All values can be overridden via environment variables or a .env file.
    The DATABASE_URL determines which async driver is used at runtime:
      - sqlite+aiosqlite:///...   → local development (no Docker required)
      - postgresql+asyncpg://...  → production / Docker
    Domain code must never branch on the database driver.
    """

    # Application
    APP_NAME: str = "AI Habitat"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./ai_habitat.db"

    # AI Provider
    AI_PROVIDER: str = "mock"
    AI_API_KEY: str = ""
    AI_MODEL: str = ""

    # CORS — comma-separated origins
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
