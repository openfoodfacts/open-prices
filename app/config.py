from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"


class LoggingLevel(Enum):
    NOTSET: str = "NOTSET"
    DEBUG: str = "DEBUG"
    INFO: str = "INFO"
    WARNING: str = "WARNING"
    ERROR: str = "ERROR"
    CRITICAL: str = "CRITICAL"

    def to_int(self):
        if self is LoggingLevel.NOTSET:
            return 0
        elif self is LoggingLevel.DEBUG:
            return 10
        elif self is LoggingLevel.INFO:
            return 20
        elif self is LoggingLevel.WARNING:
            return 30
        elif self is LoggingLevel.ERROR:
            return 40
        elif self is LoggingLevel.CRITICAL:
            return 50


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432
    cors_allow_origins: list = []
    oauth2_server_url: str | None = None
    sentry_dns: str | None = None
    log_level: LoggingLevel = LoggingLevel.INFO
    images_dir: Path = DATA_DIR / "images"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
settings.images_dir.mkdir(parents=True, exist_ok=True)
