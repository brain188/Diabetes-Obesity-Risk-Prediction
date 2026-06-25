"""
Application configuration.

Loads configuration from environment variables using Pydantic Settings.

Supports:
- Local development
- Docker
- Production deployment

No secrets are hardcoded.
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ======================================================================
    # Application
    # ======================================================================

    APP_NAME: str = "Diabetes DSS API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Intelligent Decision Support System for Early Risk Prediction "
        "of Type 2 Diabetes and Obesity"
    )

    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ======================================================================
    # API
    # ======================================================================

    API_V1_PREFIX: str = "/api/v1"

    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:4200",
    ]

    # ======================================================================
    # Database
    # ======================================================================

    DATABASE_URL: str

    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # ======================================================================
    # Authentication
    # ======================================================================

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    BCRYPT_ROUNDS: int = 12

    # ======================================================================
    # Machine Learning
    # ======================================================================

    ML_ARTIFACTS_BASE: Path = Path("../model/diabobesity-prediction/data")

    @computed_field
    @property
    def TRAINED_MODEL_PATH(self) -> Path:
        return self.ML_ARTIFACTS_BASE / "06_models" / "trained_model.pkl"

    @computed_field
    @property
    def SCALER_PATH(self) -> Path:
        return self.ML_ARTIFACTS_BASE / "06_models" / "scaler.pkl"

    @computed_field
    @property
    def SHAP_EXPLAINER_PATH(self) -> Path:
        return self.ML_ARTIFACTS_BASE / "06_models" / "shap_explainer.pkl"

    @computed_field
    @property
    def LIME_BACKGROUND_PATH(self) -> Path:
        return self.ML_ARTIFACTS_BASE / "06_models" / "lime_background.pkl"

    @computed_field
    @property
    def MODEL_METADATA_PATH(self) -> Path:
        return self.ML_ARTIFACTS_BASE / "08_reporting" / "model_metadata.json"

    @computed_field
    @property
    def EVAL_REPORT_PATH(self) -> Path:
        return self.ML_ARTIFACTS_BASE / "08_reporting" / "full_evaluation_report.json"

    MODEL_VERSION: str = "1.0.0"

    # ======================================================================
    # Model Features
    # ======================================================================

    FEATURE_NAMES: List[str] = [
        "age",
        "sex",
        "is_pregnant",
        "bmi",
        "bmi_category",
        "family_history_diabetes",
        "previous_gdm",
        "physically_active",
        "has_hypertension",
        "residence",
    ]

    SEX_MAP: Dict[str, int] = {
        "Male": 0,
        "Female": 1,
    }

    BMI_CATEGORY_MAP: Dict[str, int] = {
        "Normal": 0,
        "Overweight": 1,
        "Obese I": 2,
        "Obese II": 3,
    }

    RESIDENCE_MAP: Dict[str, int] = {
        "Urban": 1,
        "Rural": 0,
    }

    FAMILY_HISTORY_MAP: Dict[bool, int] = {
        False: 0,
        True: 1,
    }

    GDM_MAP: Dict[bool, int] = {
        False: 0,
        True: 1,
    }

    PHYSICAL_ACTIVITY_MAP: Dict[bool, int] = {
        False: 0,
        True: 1,
    }

    HYPERTENSION_MAP: Dict[bool, int] = {
        False: 0,
        True: 1,
    }

    # ======================================================================
    # Reports
    # ======================================================================

    REPORTS_DIR: Path = Path("reports")
    REPORT_MAX_SIZE_MB: int = 10

    # ======================================================================
    # Session
    # ======================================================================

    SESSION_TIMEOUT_MINUTES: int = 30

    # ======================================================================
    # Logging
    # ======================================================================

    LOG_LEVEL: str = "INFO"

    LOG_FILE: Path = Path("logs/app.log")

    LOG_FORMAT: str = (
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # ======================================================================
    # Rate Limiting
    # ======================================================================

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # ======================================================================
    # Pydantic
    # ======================================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ======================================================================
    # Helpers
    # ======================================================================

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"

    @property
    def is_staging(self) -> bool:
        return self.ENVIRONMENT.lower() == "staging"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if stripped.startswith("["):
                import json
                return json.loads(stripped)
            return [origin.strip() for origin in stripped.split(",")]
        return value

@lru_cache
def get_settings() -> Settings:
    """
    Cached settings instance.

    The configuration file is read only once during application startup.
    """
    return Settings()


settings = get_settings()