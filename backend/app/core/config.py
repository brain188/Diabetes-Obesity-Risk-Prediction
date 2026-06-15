"""
Central configuration using Pydantic Settings.
All environment variables are read from a .env file.
No hardcoded secrets anywhere in the codebase.
"""

from functools import lru_cache
from pathlib import Path
from typing import List, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Diabetes DSS API"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "Intelligent Decision Support System for Early Risk Prediction "
        "of Type 2 Diabetes and Obesity"
    )
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development | staging | production

    # API
    API_V1_PREFIX: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS — list of allowed frontend origins
    ALLOWED_ORIGINS: List[str] = ["http://localhost:4200"]  # Angular dev server

    # Database (Supabase PostgreSQL)
    DATABASE_URL: str  # e.g. postgresql+asyncpg://user:pass@host:5432/dbname
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # JWT Authentication
    SECRET_KEY: str           # Long random string — generate with: openssl rand -hex 32
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60        # 1 hour   
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30

    # Password hashing
    BCRYPT_ROUNDS: int = 12

    # ML Artifacts
    # Path to the model directory produced by the Kedro pipelines
    ML_ARTIFACTS_DIR: Path = Path("../model/kedro_project/data")
    TRAINED_MODEL_PATH: Path = Path("../model/kedro_project/data/06_models/trained_model.pkl")
    SCALER_PATH: Path = Path("../model/kedro_project/data/06_models/scaler.pkl")
    SHAP_EXPLAINER_PATH: Path = Path("../model/kedro_project/data/06_models/shap_explainer.pkl")
    MODEL_METADATA_PATH: Path = Path("../model/kedro_project/data/08_reporting/model_metadata.json")
    EVAL_REPORT_PATH: Path = Path("../model/kedro_project/data/08_reporting/full_evaluation_report.json")
    
    # Model version tracking
    MODEL_VERSION: str = "1.0.0"
    
    # Feature names expected by the model
    FEATURE_NAMES: List[str] = [
        "age", "sex", "is_pregnant", "bmi", "bmi_category",
        "family_history_diabetes", "previous_gdm", "physically_active",
        "has_hypertension", "residence"
    ]

    # Feature Encoding Maps
    # These match your training data encoding
    SEX_MAP: Dict[str, int] = {"Male": 0, "Female": 1}
    BMI_CATEGORY_MAP: Dict[str, int] = {
        "Normal": 0,
        "Overweight": 1,
        "Obese I": 2,
        "Obese II": 3
    }
    RESIDENCE_MAP: Dict[str, int] = {"Urban": 1, "Rural": 0}
    FAMILY_HISTORY_MAP: Dict[bool, int] = {False: 0, True: 1}
    GDM_MAP: Dict[bool, int] = {False: 0, True: 1}
    PHYSICAL_ACTIVITY_MAP: Dict[bool, int] = {False: 0, True: 1}
    HYPERTENSION_MAP: Dict[bool, int] = {False: 0, True: 1}

    # Report Storage
    REPORTS_DIR: Path = Path("reports")   # Where generated PDFs are saved
    REPORT_MAX_SIZE_MB: int = 10

    # Session
    SESSION_TIMEOUT_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Path = Path("logs/app.log")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Pydantic Config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Computed Properties
    @property
    def is_development(self) -> bool:
        """Return True if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Return True if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_staging(self) -> bool:
        """Return True if running in staging environment."""
        return self.ENVIRONMENT == "staging"


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings instance.
    lru_cache ensures the .env file is read only once at startup.
    """
    return Settings()


# Module-level shortcut used throughout the app
settings = get_settings()