from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "HeartGuard AI"
    APP_ENV: str = "development"
    API_PREFIX: str = "/api"

    ENCRYPTION_KEY: str = ""
    JWT_SECRET_KEY: str = "CHANGE_ME_JWT_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    COOKIE_SECURE: bool = False
    AUDIT_SALT: str = "CHANGE_ME_AUDIT_SALT"

    DATABASE_URL: str = f"sqlite:///{BACKEND_DIR / 'heartguard.db'}"

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_PREDICTION: str = "30/minute"

    DATASET_PATH: Path = BACKEND_DIR / "datasets" / "heart.csv"
    MODELS_DIR: Path = BACKEND_DIR / "models"
    ENCRYPTED_MODELS_DIR: Path = BACKEND_DIR / "encrypted_models"
    METRICS_PATH: Path = BACKEND_DIR / "encrypted_models" / "metrics.json"
    MODEL_VERSION: str = "heart-disease-model-v2"

    FRONTEND_DIST_DIR: Path = PROJECT_ROOT / "frontend" / "dist"

    MAX_PAYLOAD_BYTES: int = 50_000

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    return Settings()
