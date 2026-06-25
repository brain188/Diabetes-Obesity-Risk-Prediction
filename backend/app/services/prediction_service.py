"""
Risk prediction business logic using ML module.
"""

import asyncio
import functools
import logging
import time
from typing import Optional, Dict, Any

from app.core.exceptions import PredictionError, InputValidationError, ModelNotLoadedError
from app.core.constants import get_risk_color, RISK_HIGH, RISK_MODERATE, RISK_LOW

# ML Module Imports
from app.ml.model_loader import model_loader
from app.ml.feature_builder import PatientFeatures, build_feature_row
from app.ml.diabetes_predictor import predict_diabetes
from app.ml.obesity import assess_obesity
from app.ml.explainers import (
    explain_with_shap,
    explain_with_lime,
    FeatureContribution,
)

from app.repositories.prediction_repository import PredictionRepository
from app.repositories.screening_repository import ScreeningRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.prediction import (
    PredictionResponse,
    DiabetesPrediction,
    ObesityPrediction
)

from app.schemas.shap import (
    SHAPExplanationResponse,
    LIMEExplanationResponse,
    GlobalFeatureImportanceResponse,
    FeatureContribution as FeatureContributionSchema
)
from app.schemas.recommendation import RecommendationResponse

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for risk prediction using your ML module."""
    
    def __init__(self, session):
        """
        Initialize prediction service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.prediction_repo = PredictionRepository(session)
        self.screening_repo = ScreeningRepository(session)
        self.patient_repo = PatientRepository(session)
        self.audit_repo = AuditLogRepository(session)
        
        # Get the singleton model loader instance
        self.model_loader = model_loader
    
    async def predict_risk(
        self,
        visit_id: str,
        worker_id: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> PredictionResponse:
        """
        Run risk predictions for a screening visit using your ML module.
        
        Args:
            visit_id: Screening visit identifier
            worker_id: Healthcare worker requesting prediction
            ip_address: Client IP for audit
            request_id: Request ID for tracing
            
        Returns:
            Prediction response with diabetes and obesity risks

        Raises:
            PredictionError: If prediction fails
            ValidationError: If screening data is invalid
        """
        start_time = time.time()

        # ── Initialize all response variables to None ──────────────────────────
        shap_explanation_response = None
        lime_explanation_response = None
        global_importance_response = None
        recommendation_response = None
        
        try:
            # Get screening data
            visit = await self.screening_repo.get_visit_with_data_or_fail(
                visit_id, 
                include_patient=True
            )
            
            if not visit.screening_data:
                raise InputValidationError("No screening data found for this visit")
            
            screening_data = visit.screening_data
            patient = visit.patient
            
            # Build features
            try:
                # Build PatientFeatures using ML module's factory method
                patient_features = PatientFeatures.from_screening_data(
                    screening_data=screening_data,
                    patient_sex=patient.sex
                )

                # Build scaled feature row
                feature_row = build_feature_row(patient_features, self.model_loader)

            except ModelNotLoadedError:
                # ML artifacts weren't loaded at startup (common in test envs)
                # Return 503 instead of mapping to 422.
                raise
            except Exception as e:
                logger.error(f"Feature building failed: {str(e)}")
                raise InputValidationError(f"Failed to prepare features: {str(e)}")
            
            # Run Diabetes Prediction
            try:
                diabetes_result = predict_diabetes(feature_row, self.model_loader)
            except PredictionError as e:
                # Explicitly catch and re-raise PredictionError with context
                logger.error(f"Diabetes prediction failed for visit {visit_id}: {str(e)}")
                raise PredictionError(
                    f"Diabetes prediction failed for visit {visit_id}: {str(e)}"
                )
            except Exception as e:
                # Catch any other unexpected errors
                logger.error(f"Unexpected error in diabetes prediction: {str(e)}")
                raise PredictionError(
                    f"Unexpected error in diabetes prediction: {str(e)}"
                )
            
            # Run Obesity Assessment
            try:
                obesity_result = assess_obesity(
                    weight=screening_data.weight,
                    height=screening_data.height
                )
            except Exception as e:
                logger.error(f"Obesity assessment failed: {str(e)}")
                raise PredictionError(f"Obesity assessment failed: {str(e)}")
            
            # Calculate Latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Save to Database
            try:
                prediction = await self.prediction_repo.save_prediction(
                    visit_id=visit_id,
                    diabetes_probability=diabetes_result["diabetes_probability"],
                    diabetes_risk_class=diabetes_result["diabetes_risk_class"],
                    diabetes_class=diabetes_result["diabetes_class"],
                    obesity_probability=obesity_result["obesity_probability"],
                    obesity_risk_class=obesity_result["risk_class"],
                    obesity_class=obesity_result["obesity_class"],
                    model_version=diabetes_result["model_version"],
                    latency_ms=latency_ms
                )
            except Exception as e:
                logger.error(f"Failed to save prediction: {str(e)}")
                raise PredictionError(f"Failed to save prediction: {str(e)}")
            
            # --- Generate Recommendations ------------------------------------------
            try:
                recommendation = await self._generate_recommendations(
                    prediction_id=prediction.prediction_id,
                    diabetes_result=diabetes_result,
                    obesity_result=obesity_result
                )

                # Create recommendation response
                if recommendation:
                    recommendation_response = RecommendationResponse(
                        recommendation_id=recommendation.recommendation_id,
                        prediction_id=recommendation.prediction_id,
                        priority=recommendation.priority,
                        action_text=recommendation.action_text,
                        patient_advice=recommendation.patient_advice,
                        follow_up_interval_days=recommendation.follow_up_interval_days,
                        referral_required=recommendation.referral_required
                    )

            except Exception as e:
                logger.warning(f"Failed to generate recommendations: {str(e)}")
                # Don't fail the whole prediction if recommendations fail
            
            # ------ Generate Explanations (SHAP + LIME run concurrently) ---------------
            shap_result, lime_result = await asyncio.gather(
                self._generate_shap_explanation(
                    prediction_id=prediction.prediction_id,
                    feature_row=feature_row,
                    diabetes_result=diabetes_result
                ),
                self._generate_lime_explanation(
                    prediction_id=prediction.prediction_id,
                    feature_row=feature_row,
                    diabetes_result=diabetes_result
                ),
                return_exceptions=True,
            )

            shap_data = None if isinstance(shap_result, Exception) else shap_result
            if isinstance(shap_result, Exception):
                logger.warning(f"SHAP explanation failed: {shap_result}")
            if shap_data:
                shap_explanation_response = SHAPExplanationResponse(
                    explanation_id=shap_data["explanation_id"],
                    prediction_id=prediction.prediction_id,
                    base_value=shap_data["base_value"],
                    final_probability=diabetes_result["diabetes_probability"],
                    feature_contributions=shap_data["feature_contributions"],
                    top_positive_features=shap_data["top_positive"],
                    top_negative_features=shap_data["top_negative"]
                )

            lime_data = None if isinstance(lime_result, Exception) else lime_result
            if isinstance(lime_result, Exception):
                logger.warning(f"LIME explanation failed: {lime_result}")
            if lime_data:
                lime_explanation_response = LIMEExplanationResponse(
                    explanation_id=lime_data["explanation_id"],
                    prediction_id=prediction.prediction_id,
                    feature_contributions=lime_data["feature_contributions"],
                    top_positive_features=lime_data["top_positive"],
                    top_negative_features=lime_data["top_negative"]
                )
            
            # 3. Native Feature Importance (global, model-specific)
            try:
                global_data = await self._get_global_feature_importance_response()
                if global_data:
                    global_importance_response = global_data
            except Exception as e:
                logger.warning(f"Failed to load global feature importance: {str(e)}")
                # Don't fail the whole prediction if global importance fails
            
            # Log Prediction
            try:
                await self.audit_repo.log_prediction(
                    worker_id=worker_id,
                    patient_id=patient.patient_id,
                    diabetes_risk=diabetes_result["diabetes_risk_class"],
                    obesity_risk=obesity_result["risk_class"],
                    ip_address=ip_address,
                    request_id=request_id
                )
            except Exception as e:
                logger.warning(f"Failed to log prediction audit: {str(e)}")
                # Don't fail the whole prediction if audit fails
            
            logger.info(f"Prediction completed for visit {visit_id} in {latency_ms:.2f}ms")
            
            # ── Build Response with Explanations ──────────────────────────

            return PredictionResponse(
                prediction_id=prediction.prediction_id,
                visit_id=visit_id,
                patient_id=patient.patient_id,
                diabetes=DiabetesPrediction(
                    probability=diabetes_result["diabetes_probability"],
                    risk_class=diabetes_result["diabetes_risk_class"],
                    risk_color=get_risk_color(diabetes_result["diabetes_risk_class"]),
                    class_label=diabetes_result["diabetes_class"]
                ),
                obesity=ObesityPrediction(
                    bmi=obesity_result["bmi"],
                    bmi_category=obesity_result["bmi_category"],
                    risk_class=obesity_result["risk_class"],
                    risk_color=get_risk_color(obesity_result["risk_class"]),
                    obesity_class=obesity_result["obesity_class"]
                ),
                model_version=diabetes_result["model_version"],
                prediction_date=prediction.prediction_date,
                latency_ms=latency_ms,
                shap_explanation=shap_explanation_response,
                lime_explanation=lime_explanation_response,
                global_feature_importance=global_importance_response,
                recommendation=recommendation_response
            )
            
        except (PredictionError, InputValidationError, ModelNotLoadedError):
            # Re-raise these as they are already proper exceptions
            raise
        except Exception as e:
            # Catch any other unexpected errors
            logger.error(f"Unexpected error in prediction service: {str(e)}")
            raise PredictionError(
                f"Prediction failed for visit {visit_id}: {str(e)}"
            )
    
    # ----- Recommendations --------------------------------------
    
    async def _generate_recommendations(
        self,
        prediction_id: str,
        diabetes_result: Dict[str, Any],
        obesity_result: Dict[str, Any]
    ) -> None:
        """
        Generate clinical recommendations based on risk levels.
        
        Args:
            prediction_id: Prediction identifier
            diabetes_result: Diabetes prediction results
            obesity_result: Obesity prediction results
        """
        # Determine priority based on highest risk
        risk_levels = {
            RISK_HIGH: 3,
            RISK_MODERATE: 2,
            RISK_LOW: 1
        }
        
        diabetes_priority = risk_levels.get(diabetes_result["diabetes_risk_class"], 1)
        obesity_priority = risk_levels.get(obesity_result["risk_class"], 1)
        max_priority = max(diabetes_priority, obesity_priority)
        
        if max_priority == 3:
            priority = "High"
        elif max_priority == 2:
            priority = "Medium"
        else:
            priority = "Low"
        
        # Build recommendation text
        action_text = self._build_recommendation_text(diabetes_result, obesity_result)
        patient_advice = self._build_patient_advice(diabetes_result, obesity_result)
        
        # Determine follow-up interval
        follow_up_days = 30 if max_priority == 3 else 90 if max_priority == 2 else 180
        
        # Diabetes-specific guidance
        diabetes_guidance = self._get_diabetes_guidance(diabetes_result["diabetes_risk_class"])
        obesity_guidance = self._get_obesity_guidance(obesity_result["risk_class"])
        
        # Save recommendation
        return await self.prediction_repo.save_recommendation(
            prediction_id=prediction_id,
            priority=priority,
            action_text=action_text,
            patient_advice=patient_advice,
            follow_up_interval_days=follow_up_days,
            diabetes_guidance=diabetes_guidance,
            obesity_guidance=obesity_guidance
        )
    
    def _build_recommendation_text(self, diabetes_result: Dict, obesity_result: Dict) -> str:
        """Build detailed recommendation text for healthcare worker."""
        texts = []
        
        if diabetes_result["diabetes_risk_class"] == RISK_HIGH:
            texts.append("High diabetes risk detected. Immediate clinical review recommended. "
                        "Consider ordering HbA1c or fasting glucose test.")
        elif diabetes_result["diabetes_risk_class"] == RISK_MODERATE:
            texts.append("Moderate diabetes risk. Schedule follow-up in 3 months for glucose monitoring. "
                        "Discuss lifestyle modifications.")
        else:
            texts.append("Low diabetes risk. Continue routine monitoring and health education.")
        
        if obesity_result["risk_class"] == RISK_HIGH:
            texts.append("High obesity risk. Referral to nutritionist recommended. "
                        "Discuss weight management program.")
        elif obesity_result["risk_class"] == RISK_MODERATE:
            texts.append("Overweight status. Provide dietary counseling and physical activity guidance.")
        
        return " ".join(texts)
    
    def _build_patient_advice(self, diabetes_result: Dict, obesity_result: Dict) -> str:
        """Build patient-friendly advice text."""
        texts = []
        
        if diabetes_result["diabetes_risk_class"] in [RISK_MODERATE, RISK_HIGH]:
            texts.append("• Reduce sugar and refined carbohydrate intake")
            texts.append("• Increase physical activity to at least 30 minutes daily")
            texts.append("• Monitor for symptoms like increased thirst and frequent urination")
        
        if obesity_result["risk_class"] in [RISK_MODERATE, RISK_HIGH]:
            texts.append("• Aim for gradual weight loss (1-2 kg per month)")
            texts.append("• Eat more vegetables and whole grains")
            texts.append("• Limit processed foods and sugary drinks")
        
        if not texts:
            texts.append("• Maintain healthy lifestyle with balanced diet and regular exercise")
            texts.append("• Schedule regular health check-ups")
        
        return "\n".join(texts)
    
    def _get_diabetes_guidance(self, risk_class: str) -> str:
        """Get diabetes-specific clinical guidance."""
        if risk_class == RISK_HIGH:
            return ("Consider initiating diabetes screening protocol. "
                   "Monitor blood glucose. Assess for diabetes complications.")
        elif risk_class == RISK_MODERATE:
            return ("Provide diabetes prevention education. "
                   "Encourage weight management and physical activity.")
        else:
            return ("Continue routine diabetes screening per guidelines. "
                   "Reinforce healthy lifestyle choices.")
    
    def _get_obesity_guidance(self, risk_class: str) -> str:
        """Get obesity-specific clinical guidance."""
        if risk_class == RISK_HIGH:
            return ("Comprehensive weight management program recommended. "
                   "Consider medication referral for severe obesity.")
        elif risk_class == RISK_MODERATE:
            return ("Dietary counseling and physical activity prescription. "
                   "Monitor weight at each visit.")
        else:
            return ("Maintain healthy weight through balanced nutrition and exercise.")
    
    # ----- SHAP Explanation -----------------------------------------------
    
    async def _generate_shap_explanation(
        self,
        prediction_id: str,
        feature_row,
        diabetes_result: Dict[str, Any]
    ) -> None:
        """
        Generate SHAP explanation using your ML module.
        
        Args:
            prediction_id: Prediction identifier
            feature_row: Scaled feature DataFrame
            diabetes_result: Diabetes prediction results
        """
        try:
            loop = asyncio.get_running_loop()
            top_positive, top_negative, base_value, feature_contributions = await loop.run_in_executor(
                None, explain_with_shap, feature_row, self.model_loader
            )
            
            # Save SHAP explanation
            shap_explanation = await self.prediction_repo.save_shap_explanation(
                prediction_id=prediction_id,
                base_value=base_value,
                feature_contributions=feature_contributions,
                top_positive_features=top_positive,
                top_negative_features=top_negative,
                method="SHAP"
            )

            # feature_contributions is a flat dict {feature_name: shap_value}
            feature_contribs = [
                FeatureContributionSchema(
                    feature_name=feat,
                    value=0.0,
                    shap_value=sv,
                    impact_direction="Positive" if sv > 0 else "Negative",
                    importance_abs=abs(sv)
                )
                for feat, sv in feature_contributions.items()
            ]
            
            top_pos = [
                FeatureContributionSchema(
                    feature_name=f["feature_name"],
                    value=f["value"],
                    shap_value=f["shap_value"],
                    impact_direction=f["impact_direction"],
                    importance_abs=f["importance_abs"]
                )
                for f in top_positive
            ]
            
            top_neg = [
                FeatureContributionSchema(
                    feature_name=f["feature_name"],
                    value=f["value"],
                    shap_value=f["shap_value"],
                    impact_direction=f["impact_direction"],
                    importance_abs=f["importance_abs"]
                )
                for f in top_negative
            ]
            
            return {
                "explanation_id": shap_explanation.explanation_id,
                "base_value": base_value,
                "feature_contributions": feature_contribs,
                "top_positive": top_pos,
                "top_negative": top_neg
            }
            
        except Exception as e:
            import traceback
            logger.warning(
                "Failed to generate SHAP explanation: %s\n%s",
                str(e), traceback.format_exc()
            )
            # Don't raise - explanation is optional

    # ------ LIME Explanation ------------------------------------------------
    
    async def _generate_lime_explanation(
        self,
        prediction_id: str,
        feature_row,
        diabetes_result: Dict[str, Any]
    ) -> None:
        """
        Generate LIME explanation using your ML module.
        
        LIME provides a complementary model-agnostic explanation.
        
        Args:
            prediction_id: Prediction identifier
            feature_row: Scaled feature DataFrame
            diabetes_result: Diabetes prediction results
        """
        try:
            # Get background data from ModelLoader (now cached in model_loader)
            background_data = self.model_loader.get_background()
            
            if background_data is None:
                logger.warning("Background data not available for LIME, skipping")
                return None
            
            loop = asyncio.get_running_loop()
            lime_contributions = await loop.run_in_executor(
                None,
                functools.partial(explain_with_lime, feature_row, background_data, self.model_loader, 200)
            )
            
            # Convert to feature contributions dict
            feature_contributions = {
                c["feature_name"]: c["shap_value"] 
                for c in lime_contributions
            }
            
            # Separate positive and negative contributions
            top_positive = [c for c in lime_contributions if c["impact_direction"] == "Positive"]
            top_negative = [c for c in lime_contributions if c["impact_direction"] == "Negative"]

            # LIME is not persisted — shap_explanations has a unique constraint on
            # prediction_id, and SHAP already owns that row. LIME is always recomputed
            # fresh so there is no need for a separate DB row.
            import uuid
            lime_explanation_id = str(uuid.uuid4())

            feature_contribs = [
                FeatureContributionSchema(
                    feature_name=c["feature_name"],
                    value=c["value"],
                    shap_value=c["shap_value"],
                    impact_direction=c["impact_direction"],
                    importance_abs=c["importance_abs"]
                )
                for c in lime_contributions
            ]

            top_pos = [
                FeatureContributionSchema(
                    feature_name=c["feature_name"],
                    value=c["value"],
                    shap_value=c["shap_value"],
                    impact_direction=c["impact_direction"],
                    importance_abs=c["importance_abs"]
                )
                for c in top_positive
            ]

            top_neg = [
                FeatureContributionSchema(
                    feature_name=c["feature_name"],
                    value=c["value"],
                    shap_value=c["shap_value"],
                    impact_direction=c["impact_direction"],
                    importance_abs=c["importance_abs"]
                )
                for c in top_negative
            ]

            return {
                "explanation_id": lime_explanation_id,
                "feature_contributions": feature_contribs,
                "top_positive": top_pos,
                "top_negative": top_neg
            }
            
        except ImportError:
            logger.warning("LIME library not installed, skipping LIME explanation")
        except Exception as e:
            logger.warning(f"Failed to generate LIME explanation: {str(e)}")
            # Don't raise - explanation is optional
    
    # ----- Global Feature Importance ----------------------------------------
    
    async def _get_global_feature_importance_response(self):
        try:
            importance_list, method = self.model_loader.get_feature_importance_cached()
            
            return GlobalFeatureImportanceResponse(
                model_version=self.model_loader.model_version,
                feature_importance={
                    item["feature"]: item["importance"]
                    for item in importance_list
                },
                sorted_features=[
                    item["feature"]
                    for item in importance_list
                ],
                method=method,
                updated_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            )
        except Exception as e:
            logger.warning(f"Failed to get global feature importance: {str(e)}")
            return None

    
    async def get_global_feature_importance(self) -> Dict[str, Any]:
        """Get global feature importance (public method for API endpoint)."""
        importance_list, method = self.model_loader.get_feature_importance_cached()
        return {
            "importance": importance_list,
            "method": method,
            "model_version": self.model_loader.model_version,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }