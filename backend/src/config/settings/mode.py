import enum
from src.config.settings.base import BackendBaseSettings


class Environment(str, enum.Enum):
    PRODUCTION: str = "PROD"  # type: ignore
    DEVELOPMENT: str = "DEV"  # type: ignore
    STAGING: str = "STAGE"  # type:ignore


class BackendDevSettings(BackendBaseSettings):
    DESCRIPTION: str | None = "Development Environment."
    DEBUG: bool = True
    ENVIRONMENT: Environment = Environment.DEVELOPMENT


class BackendProdSettings(BackendBaseSettings):
    DESCRIPTION: str | None = "Production Environment."
    ENVIRONMENT: Environment = Environment.PRODUCTION


class BackendStageSettings(BackendBaseSettings):
    DESCRIPTION: str | None = "Test Environment."
    DEBUG: bool = True
    ENVIRONMENT: Environment = Environment.STAGING
