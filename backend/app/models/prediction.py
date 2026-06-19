"""
Prediction model for storing ML model outputs.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base  
from app.models.base import generate_uuid

if TYPE_CHECKING:
    from app.models.screening_data import ScreeningVisit
    from app.models.recommendation import Recommendation
    from app.models.explanation import SHAPExplanation

class Prediction(Base):
    """
    Prediction results from the ML models.
    Stores both diabetes and obesity predictions for a screening visit.
    """
    
    __tablename__ = "predictions"
    
    # Primary key
    prediction_id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        doc="Unique identifier for the prediction"
    )
    
    # Foreign key to screening visit
    visit_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("screening_visits.visit_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One prediction per visit
        index=True,
        doc="Foreign key to screening visit"
    )
    
    # Diabetes prediction (from ML model)
    diabetes_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Probability of diabetes (0.0 to 1.0)"
    )
    
    diabetes_risk_class: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Risk class: Low/Moderate/High"
    )
    
    diabetes_class: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Detailed class: Normal/Prediabetes/Diabetic"
    )
    
    # Obesity prediction (from rule-based system)
    obesity_probability: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Probability of obesity (0.0 to 1.0) - derived from BMI"
    )
    
    obesity_risk_class: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Risk class: Low/Moderate/High"
    )
    
    obesity_class: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Obesity class: Normal/Overweight/Obese"
    )
    
    # Model metadata
    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Version of the model used for prediction"
    )
    
    prediction_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when prediction was made"
    )
    
    # Prediction latency tracking
    latency_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Prediction latency in milliseconds"
    )
    
    # Relationships
    visit: Mapped["ScreeningVisit"] = relationship(
        "ScreeningVisit",
        back_populates="prediction"
    )
    
    recommendation: Mapped[Optional["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="prediction",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Clinical recommendations based on this prediction"
    )
    
    shap_explanation: Mapped[Optional["SHAPExplanation"]] = relationship(
        "SHAPExplanation",
        back_populates="prediction",
        uselist=False,
        cascade="all, delete-orphan",
        doc="SHAP explanation for the diabetes prediction"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_prediction_visit", "visit_id"),
        Index("idx_prediction_date", "prediction_date"),
        Index("idx_prediction_model", "model_version"),
    )
    
    def __repr__(self) -> str:
        return f"<Prediction(prediction_id={self.prediction_id}, diabetes_prob={self.diabetes_probability})>"