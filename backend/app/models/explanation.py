"""
SHAP explanation model for model interpretability.
"""

from typing import Optional, Dict, Any

from sqlalchemy import Column, String, Float, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, generate_uuid


class SHAPExplanation(Base):
    """
    SHAP (SHapley Additive exPlanations) values for prediction interpretability.
    Helps healthcare workers understand why a prediction was made.
    """
    
    __tablename__ = "shap_explanations"
    
    # Primary key
    explanation_id = Column(
        UUID(as_uuid=False),
        primary_key=True,
        default=generate_uuid,
        nullable=False,
        doc="Unique identifier for the SHAP explanation"
    )
    
    # Foreign key to prediction
    prediction_id = Column(
        UUID(as_uuid=False),
        ForeignKey("predictions.prediction_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One explanation per prediction
        index=True,
        doc="Foreign key to prediction"
    )
    
    # SHAP values
    base_value = Column(
        Float,
        nullable=False,
        doc="Base value (expected model output)"
    )
    
    # Feature contributions as JSON
    # Format: {"feature_name": shap_value, ...}
    feature_contributions = Column(
        JSON,
        nullable=False,
        doc="Dictionary mapping feature names to SHAP values"
    )
    
    # Top contributing features (positive and negative)
    top_positive_features = Column(
        JSON,
        nullable=True,
        doc="Top 5 features that increased risk (with values)"
    )
    
    top_negative_features = Column(
        JSON,
        nullable=True,
        doc="Top 5 features that decreased risk (with values)"
    )
    
    # Explanation method
    method = Column(
        String(50),
        default="SHAP",
        nullable=False,
        doc="Explanation method used (SHAP, LIME, etc.)"
    )
    
    # Visualization data (optional)
    force_plot_data = Column(
        JSON,
        nullable=True,
        doc="Force plot data for visualization"
    )
    
    waterfall_data = Column(
        JSON,
        nullable=True,
        doc="Waterfall plot data for visualization"
    )
    
    # Relationships
    prediction = relationship(
        "Prediction",
        back_populates="shap_explanation"
    )
    
    # Indexes
    __table_args__ = (
        Index("idx_shap_prediction", "prediction_id"),
    )
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get sorted feature importance (absolute values)."""
        if not self.feature_contributions:
            return {}
        
        # Sort by absolute value descending
        sorted_features = sorted(
            self.feature_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        return dict(sorted_features)
    
    def __repr__(self) -> str:
        return f"<SHAPExplanation(explanation_id={self.explanation_id}, prediction_id={self.prediction_id})>"