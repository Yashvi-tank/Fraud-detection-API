"""Application configuration loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    APP_NAME: str = "Fraud Detection API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/fraud_detection"
    )

    # Behavioral fraud — velocity detection
    VELOCITY_SHORT_WINDOW_MINUTES: int = 2
    VELOCITY_SHORT_WINDOW_MAX_COUNT: int = 3
    VELOCITY_SHORT_WINDOW_SCORE: int = 20

    VELOCITY_LONG_WINDOW_MINUTES: int = 10
    VELOCITY_LONG_WINDOW_MAX_COUNT: int = 5
    VELOCITY_LONG_WINDOW_SCORE: int = 15

    # Behavioral fraud — country change detection
    COUNTRY_CHANGE_SCORE: int = 20

    # Behavioral fraud — device history
    NEW_DEVICE_SCORE: int = 15

    # Behavioral fraud — spending pattern
    SPENDING_ANOMALY_MIN_PRIOR_TRANSACTIONS: int = 3
    SPENDING_ANOMALY_MULTIPLIER: float = 3.0
    SPENDING_ANOMALY_SCORE: int = 25

    # ML fraud detection
    ML_MODEL_PATH: str = "app/ml/models/fraud_model.joblib"
    ML_MODEL_METADATA_PATH: str = "app/ml/models/model_metadata.json"
    ML_WEIGHT: int = 20
    ML_ENABLED: bool = True

    # Security & Authentication
    JWT_SECRET_KEY: str = "super_secret_jwt_key_for_dev_change_me_in_prod"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()
