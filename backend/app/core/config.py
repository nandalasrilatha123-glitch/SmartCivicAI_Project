"""
Centralized application configuration.
All values are read from environment variables (see .env.example).
Never hard-code secrets here.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "SmartCivicAI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # Database
    DATABASE_URL: str = "postgresql+psycopg://smartcivic_user:smartcivic_pass@localhost:5432/smartcivicai"

    # Auth
    JWT_SECRET_KEY: str = "CHANGE_ME_TO_A_LONG_RANDOM_SECRET"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # AI
    AI_PROVIDER: str = "demo"  # demo | anthropic (openai not implemented — falls back to demo with a logged reason)
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    AI_MODEL_NAME: str = "claude-sonnet-4-6"
    AI_CONFIDENCE_THRESHOLD: float = 0.55

    # CV
    CV_PROVIDER: str = "demo"  # demo | yolo
    YOLO_WEIGHTS_PATH: str = "models/yolo/civic_issues.pt"

    # Predictive analytics
    PREDICTION_PROVIDER: str = "demo"  # demo | sklearn | xgboost

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    APP_EMAIL: str = "smartcivicai.project@gmail.com"
    ADMIN_EMAIL: str = "nandalasrilatha123@gmail.com"
    EMAIL_PASSWORD: str = "Srilatha@123"
    EMAIL_ENABLED: bool = False

    # Maps
    GOOGLE_MAPS_API_KEY: str = ""

    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 8
    UPLOAD_DIR: str = "uploads"
    ALLOWED_IMAGE_EXTENSIONS: str = ".jpg,.jpeg,.png,.webp"

    @property
    def allowed_image_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_IMAGE_EXTENSIONS.split(",")]

    @property
    def cors_origins(self) -> List[str]:
        return [self.FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
