"""
Repository for Prediction and related model operations.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.prediction import Prediction
from app.models.recommendation import Recommendation
from app.models.explanation import SHAPExplanation
from app.repositories.base import BaseRepository
from app.models.screening_data import ScreeningVisit

logger = logging.getLogger(__name__)


class PredictionRepository:
    """Repository for prediction-related operations."""
    
    def __init__(self, session):
        self.session = session
        self.prediction_repo = BaseRepository(Prediction, session)
        self.recommendation_repo = BaseRepository(Recommendation, session)
        self.shap_repo = BaseRepository(SHAPExplanation, session)
    
    async def save_prediction(
        self,
        visit_id: str,
        diabetes_probability: float,
        diabetes_risk_class: str,
        diabetes_class: str,
        obesity_probability: float,
        obesity_risk_class: str,
        obesity_class: str,
        model_version: str,
        latency_ms: Optional[float] = None
    ) -> Prediction:
        """
        Save prediction results for a screening visit.
        
        Args:
            visit_id: Screening visit identifier
            diabetes_probability: Probability of diabetes (0-1)
            diabetes_risk_class: Low/Moderate/High
            diabetes_class: Normal/Prediabetes/Diabetic
            obesity_probability: Probability of obesity (0-1)
            obesity_risk_class: Low/Moderate/High
            obesity_class: Normal/Overweight/Obese
            model_version: Model version used
            latency_ms: Prediction latency in milliseconds
            
        Returns:
            Created Prediction instance
        """
        prediction = await self.prediction_repo.create(
            visit_id=visit_id,
            diabetes_probability=diabetes_probability,
            diabetes_risk_class=diabetes_risk_class,
            diabetes_class=diabetes_class,
            obesity_probability=obesity_probability,
            obesity_risk_class=obesity_risk_class,
            obesity_class=obesity_class,
            model_version=model_version,
            latency_ms=latency_ms,
            prediction_date=datetime.now(timezone.utc)
        )
        
        logger.info(f"Saved prediction for visit {visit_id}: diabetes_risk={diabetes_risk_class}")
        return prediction
    
    async def get_prediction_with_details(
        self,
        prediction_id: str
    ) -> Optional[Prediction]:
        """
        Get prediction with its recommendation and SHAP explanation.
        
        Args:
            prediction_id: Prediction identifier
            
        Returns:
            Prediction instance with loaded relationships
        """
        try:
            stmt = (
                select(Prediction)
                .where(Prediction.prediction_id == prediction_id)
                .options(
                    # direct relationships used by API serialization
                    selectinload(Prediction.visit).selectinload(ScreeningVisit.screening_data),
                    selectinload(Prediction.visit).selectinload(ScreeningVisit.patient),
                    # other optional relationships
                    selectinload(Prediction.recommendation),
                    selectinload(Prediction.shap_explanation),
                )
            )
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get prediction {prediction_id} with details: {str(e)}")
            raise
    
    async def get_prediction_by_visit(
        self,
        visit_id: str,
        include_details: bool = False
    ) -> Optional[Prediction]:
        """
        Get prediction by visit ID.
        
        Args:
            visit_id: Screening visit identifier
            include_details: Whether to load recommendation and SHAP
            
        Returns:
            Prediction instance or None
        """
        try:
            stmt = select(Prediction).where(Prediction.visit_id == visit_id)
            
            if include_details:
                stmt = stmt.options(
                    selectinload(Prediction.recommendation),
                    selectinload(Prediction.shap_explanation)
                )
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get prediction for visit {visit_id}: {str(e)}")
            raise
    
    async def save_recommendation(
        self,
        prediction_id: str,
        priority: str,
        action_text: str,
        patient_advice: Optional[str] = None,
        follow_up_interval_days: Optional[int] = None,
        referral_required: Optional[str] = None,
        diabetes_guidance: Optional[str] = None,
        obesity_guidance: Optional[str] = None
    ) -> Recommendation:
        """
        Save clinical recommendation for a prediction.
        
        Args:
            prediction_id: Prediction identifier
            priority: Urgent/High/Medium/Low
            action_text: Detailed recommendation text
            patient_advice: Patient-friendly advice
            follow_up_interval_days: Days until follow-up
            referral_required: Specialist referral if needed
            diabetes_guidance: Diabetes-specific recommendations
            obesity_guidance: Obesity-specific recommendations
            
        Returns:
            Created Recommendation instance
        """
        recommendation = await self.recommendation_repo.create(
            prediction_id=prediction_id,
            priority=priority,
            action_text=action_text,
            patient_advice=patient_advice,
            follow_up_interval_days=follow_up_interval_days,
            referral_required=referral_required,
            diabetes_guidance=diabetes_guidance,
            obesity_guidance=obesity_guidance
        )
        
        logger.info(f"Saved recommendation for prediction {prediction_id}")
        return recommendation
    
    async def save_shap_explanation(
        self,
        prediction_id: str,
        base_value: float,
        feature_contributions: Dict[str, float],
        top_positive_features: Optional[Dict[str, Any]] = None,
        top_negative_features: Optional[Dict[str, Any]] = None,
        method: str = "SHAP"
    ) -> SHAPExplanation:
        """
        Save SHAP explanation for a prediction.
        
        Args:
            prediction_id: Prediction identifier
            base_value: Base probability value
            feature_contributions: Dictionary of feature contributions
            top_positive_features: Top risk-increasing features
            top_negative_features: Top risk-decreasing features
            method: Explanation method (default SHAP)
            
        Returns:
            Created SHAPExplanation instance
        """
        shap_explanation = await self.shap_repo.create(
            prediction_id=prediction_id,
            base_value=base_value,
            feature_contributions=feature_contributions,
            top_positive_features=top_positive_features,
            top_negative_features=top_negative_features,
            method=method
        )
        
        logger.info(f"Saved SHAP explanation for prediction {prediction_id}")
        return shap_explanation
    
    async def get_prediction_history(
        self,
        patient_id: str,
        limit: int = 10
    ) -> list:
        """
        Get prediction history for a patient.
        
        Args:
            patient_id: Patient identifier
            limit: Maximum number of predictions to return
            
        Returns:
            List of predictions with visit dates
        """
        try:
            stmt = select(
                Prediction,
                ScreeningVisit.visit_date
            ).join(
                ScreeningVisit, Prediction.visit_id == ScreeningVisit.visit_id
            ).where(
                ScreeningVisit.patient_id == patient_id
            ).order_by(
                desc(ScreeningVisit.visit_date)
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            rows = result.all()
            
            # Important: avoid accessing lazy-loaded relationships here (can trigger MissingGreenlet)
            # because this repository is building dicts after the async query has completed.
            result_items = []
            for row in rows:
                prediction_obj = row[0]
                visit_date = row[1]

                result_items.append(
                    {
                        "prediction_id": prediction_obj.prediction_id,
                        "visit_id": prediction_obj.visit_id,
                        "patient_id": None,
                        "diabetes": {
                            "probability": prediction_obj.diabetes_probability,
                            "risk_class": prediction_obj.diabetes_risk_class,
                            "class_label": prediction_obj.diabetes_class,
                        },
                        "obesity": {
                            "bmi": None,
                            "bmi_category": None,
                            "risk_class": prediction_obj.obesity_risk_class,
                            "obesity_class": prediction_obj.obesity_class,
                        },
                        "model_version": prediction_obj.model_version,
                        "prediction_date": prediction_obj.prediction_date,
                        "latency_ms": prediction_obj.latency_ms,
                        "visit_date": visit_date,
                    }
                )

            return result_items
        except Exception as e:
            logger.error(f"Failed to get prediction history for patient {patient_id}: {str(e)}")
            raise
