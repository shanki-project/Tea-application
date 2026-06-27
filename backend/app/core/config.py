"""Application configuration.

All settings are read from environment variables (or a local .env file).
See `.env.example` at the repo root for the full list and defaults.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root = .../assamtea  (config.py -> core -> app -> backend -> <root>)
BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    PROJECT_NAME: str = "ASSAM TEA"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = False
    API_PREFIX: str = "/api"

    # Comma-separated list of allowed CORS origins, e.g. "https://assamtea.com,https://www.assamtea.com"
    CORS_ORIGINS: str = "*"

    # Directory that holds the built static frontend (index.html, assets, media).
    # Overridden in Docker via the STATIC_DIR env var.
    STATIC_DIR: str = str(BASE_DIR / "public")

    # --- Database (MySQL) ---
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "assamtea"
    MYSQL_PASSWORD: str = "changeme"
    MYSQL_DB: str = "assamtea"

    # Optional: a full SQLAlchemy URL overrides the discrete fields above.
    DATABASE_URL: str | None = None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}?charset=utf8mb4"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
