"""
Recommendation model for clinical guidance based on predictions.
"""

from typing import Optional

from sqlalchemy import Column, String, Integer, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class Recommendation(Base):
    """
    Clinical recommendations generated from prediction results.
    Provides actionable guidance for healthcare workers.
    """
    
    __tablename__ = "recommendations"
    
    # Primary key
    recommendation_id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        doc="Unique identifier for the recommendation"
    )
    
    # Foreign key to prediction
    prediction_id = Column(
        UUID(as_uuid=False),
        ForeignKey("predictions.prediction_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One recommendation per prediction
        index=True,
        doc="Foreign key to prediction"
    )
    
    # Recommendation details
    priority = Column(
        String(20),
        nullable=False,
        doc="Priority level: Urgent/High/Medium/Low"
    )
    
    action_text = Column(
        Text,
        nullable=False,
        doc="Detailed recommendation text for healthcare worker"
    )
    
    patient_advice = Column(
        Text,
        nullable=True,
        doc="Patient-friendly advice text"
    )
    
    follow_up_interval_days = Column(
        Integer,
        nullable=True,
        doc="Recommended days until follow-up"
    )
    
    referral_required = Column(
        String(100),
        nullable=True,
        doc="Specialist referral required (e.g., 'Endocrinologist')"
    )
    
    # Additional context
    diabetes_guidance = Column(
        Text,
        nullable=True,
        doc="Diabetes-specific recommendations"
    )
    
    obesity_guidance = Column(
        Text,
        nullable=True,
        doc="Obesity-specific recommendations"
    )
    
    # Relationships
    prediction = relationship(
        "Prediction",
        back_populates="recommendation"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_recommendation_prediction", "prediction_id"),
        Index("idx_recommendation_priority", "priority"),
    )
    
    def __repr__(self) -> str:
        return f"<Recommendation(recommendation_id={self.recommendation_id}, priority={self.priority})>"