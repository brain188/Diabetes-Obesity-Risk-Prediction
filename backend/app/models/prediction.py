"""
Prediction model for storing ML model outputs.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class Prediction(Base):
    """
    Prediction results from the ML models.
    Stores both diabetes and obesity predictions for a screening visit.
    """
    
    __tablename__ = "predictions"
    
    # Primary key
    prediction_id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        doc="Unique identifier for the prediction"
    )
    
    # Foreign key to screening visit
    visit_id = Column(
        UUID(as_uuid=False),
        ForeignKey("screening_visits.visit_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One prediction per visit
        index=True,
        doc="Foreign key to screening visit"
    )
    
    # Diabetes prediction (from ML model)
    diabetes_probability = Column(
        Float,
        nullable=False,
        doc="Probability of diabetes (0.0 to 1.0)"
    )
    
    diabetes_risk_class = Column(
        String(20),
        nullable=False,
        doc="Risk class: Low/Moderate/High"
    )
    
    diabetes_class = Column(
        String(20),
        nullable=True,
        doc="Detailed class: Normal/Prediabetes/Diabetic"
    )
    
    # Obesity prediction (from rule-based system)
    obesity_probability = Column(
        Float,
        nullable=True,
        doc="Probability of obesity (0.0 to 1.0) - derived from BMI"
    )
    
    obesity_risk_class = Column(
        String(20),
        nullable=False,
        doc="Risk class: Low/Moderate/High"
    )
    
    obesity_class = Column(
        String(20),
        nullable=True,
        doc="Obesity class: Normal/Overweight/Obese"
    )
    
    # Model metadata
    model_version = Column(
        String(50),
        nullable=False,
        doc="Version of the model used for prediction"
    )
    
    prediction_date = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        doc="Timestamp when prediction was made"
    )
    
    # Prediction latency tracking
    latency_ms = Column(
        Float,
        nullable=True,
        doc="Prediction latency in milliseconds"
    )
    
    # Relationships
    visit = relationship(
        "ScreeningVisit",
        back_populates="prediction"
    )
    
    recommendation = relationship(
        "Recommendation",
        back_populates="prediction",
        uselist=False,
        cascade="all, delete-orphan",
        doc="Clinical recommendations based on this prediction"
    )
    
    shap_explanation = relationship(
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