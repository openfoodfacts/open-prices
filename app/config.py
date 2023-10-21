from enum import StrEnum

from pydantic_settings import BaseSettings


class LoggingLevel(StrEnum):
    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

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
    postgres_host: str
    postgres_user: str
    postgres_password: str
    postgres_db_name: str
    postgres_port: int = 5432
    sentry_dns: str | None = None
    log_level: LoggingLevel = LoggingLevel.INFO


settings = Settings()
