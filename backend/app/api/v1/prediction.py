"""
Risk prediction endpoints.
Handles diabetes and obesity risk prediction.
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.constants import get_risk_color
from app.core.dependencies import get_current_user_id, get_client_ip, get_request_metadata
from app.core.logging import get_logger
from app.schemas.prediction import PredictionResponse, PredictionRequest
from app.schemas.prediction import DiabetesPrediction, ObesityPrediction
from app.schemas.recommendation import RecommendationResponse
from app.schemas.common import SuccessResponse
from app.schemas.shap import (
    CombinedExplanationResponse, 
    SHAPExplanationResponse, 
    LIMEExplanationResponse, 
    GlobalFeatureImportanceResponse, 
    FeatureContribution
)
from app.schemas.screening import ScreeningDataRequest
from app.services.prediction_service import PredictionService
from app.services.screening_service import ScreeningService
from app.services.patient_service import PatientService
from app.core.exceptions import PredictionError, InputValidationError, NotFoundError, ModelNotLoadedError

logger = get_logger(__name__)
router = APIRouter()

# ----- POST /predictions/ ----------------------------------------------------

@router.post(
    "/",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Run risk prediction",
    description="Run diabetes and obesity risk prediction for a patient.",
)
async def predict_risk(
    request: PredictionRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
    metadata: dict = Depends(get_request_metadata),
) -> PredictionResponse:
    """
    Run risk prediction.
    
    - Predicts diabetes risk (ML model)
    - Predicts obesity risk (rule-based)
    - Generates SHAP and LIME explanations
    - Creates clinical recommendations
    - Saves all results to database
    """
    prediction_service = PredictionService(db)
    screening_service = ScreeningService(db)
    
    try:
        # Check if visit_id is provided or we need to create one
        if hasattr(request, 'visit_id') and request.visit_id:
            visit_id = request.visit_id
        else:
            # Create a new screening visit from the request data
            # First, verify patient exists
            patient_service = PatientService(db)
            
            # Check if patient exists
            try:
                patient = await patient_service.get_patient(request.patient_id)
            except NotFoundError:
                raise NotFoundError("Patient", request.patient_id)
            
            # Create screening visit
            visit_result = await screening_service.create_screening_visit(
                patient_id=request.patient_id,
                worker_id=current_user,
                notes=request.screening_data.notes if hasattr(request.screening_data, 'notes') else None,
                ip_address=client_ip
            )
            
            visit_id = visit_result["visit_id"]
            
            # Save screening data
            await screening_service.save_screening_data(
                visit_id=visit_id,
                request=request.screening_data,
                worker_id=current_user,
                ip_address=client_ip
            )
            
            logger.info(f"Created screening visit {visit_id} for prediction")
        
        if not visit_id:
            raise InputValidationError("Visit ID is required")
        
        result = await prediction_service.predict_risk(
            visit_id=visit_id,
            worker_id=current_user,
            ip_address=client_ip,
            request_id=metadata.get("request_id")
        )
        
        logger.info(f"Prediction completed: {result.prediction_id}")
        return result
        
    except NotFoundError as e:
        logger.warning(f"Prediction failed - visit not found: {str(e)}")
        raise
    except (PredictionError, InputValidationError) as e:
        logger.error(f"Prediction failed: {str(e)}")
        raise

# ---------- GET /predictions/{prediction_id} ------------------------------------------------

@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get prediction result",
    description="Get a specific prediction result by ID with all explanations and recommendations.",
)
async def get_prediction(
    prediction_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> PredictionResponse:
    """
    Get a specific prediction with all its data.
    
    - Returns prediction with all details
    - Includes diabetes and obesity results
    - Requires authentication
    """
    service = PredictionService(db)
    
    # Get prediction from repository
    prediction = await service.prediction_repo.get_prediction_with_details(prediction_id)
    
    if not prediction:
        raise NotFoundError("Prediction", prediction_id)
    
    # ── Build SHAP Explanation (from database) ─────────────────────────────
    shap_explanation_response = None
    if prediction.shap_explanation and prediction.shap_explanation.method == "SHAP":
        # Build feature contributions from stored data
        feature_contributions = []
        for feature_name, shap_value in prediction.shap_explanation.feature_contributions.items():
            feature_contributions.append(
                FeatureContribution(
                    feature_name=feature_name,
                    value=0.0,  # Value can be fetched from screening data if needed
                    shap_value=shap_value,
                    impact_direction="Positive" if shap_value > 0 else "Negative",
                    importance_abs=abs(shap_value)
                )
            )
        feature_contributions.sort(key=lambda x: x.importance_abs, reverse=True)
        top_positive = [f for f in feature_contributions if f.impact_direction == "Positive"][:5]
        top_negative = [f for f in feature_contributions if f.impact_direction == "Negative"][:5]
        
        shap_explanation_response = SHAPExplanationResponse(
            explanation_id=prediction.shap_explanation.explanation_id,
            prediction_id=prediction.prediction_id,
            base_value=prediction.shap_explanation.base_value,
            final_probability=prediction.diabetes_probability,
            feature_contributions=feature_contributions,
            top_positive_features=top_positive,
            top_negative_features=top_negative
        )
    
    # ── Build LIME Explanation (from database) ─────────────────────────────
    lime_explanation_response = None
    if prediction.shap_explanation and prediction.shap_explanation.method == "LIME":
        feature_contributions = []
        for feature_name, lime_value in prediction.shap_explanation.feature_contributions.items():
            feature_contributions.append(
                FeatureContribution(
                    feature_name=feature_name,
                    value=0.0,
                    shap_value=lime_value,
                    impact_direction="Positive" if lime_value > 0 else "Negative",
                    importance_abs=abs(lime_value)
                )
            )
        feature_contributions.sort(key=lambda x: x.importance_abs, reverse=True)
        top_positive = [f for f in feature_contributions if f.impact_direction == "Positive"][:5]
        top_negative = [f for f in feature_contributions if f.impact_direction == "Negative"][:5]
        
        lime_explanation_response = LIMEExplanationResponse(
            explanation_id=prediction.shap_explanation.explanation_id,
            prediction_id=prediction.prediction_id,
            feature_contributions=feature_contributions,
            top_positive_features=top_positive,
            top_negative_features=top_negative
        )
    
    # ── Build Global Feature Importance (from cache) ──────────────────────
    global_importance_response = None
    try:
        global_data = await service.get_global_feature_importance_response()
        if global_data:
            global_importance_response = global_data
    except Exception as e:
        logger.warning(f"Failed to get global feature importance: {str(e)}")
    
    # ── Build Recommendation (from database) ──────────────────────────────
    recommendation_response = None
    if prediction.recommendation:
        recommendation_response = RecommendationResponse(
            recommendation_id=prediction.recommendation.recommendation_id,
            prediction_id=prediction.recommendation.prediction_id,
            priority=prediction.recommendation.priority,
            action_text=prediction.recommendation.action_text,
            patient_advice=prediction.recommendation.patient_advice,
            follow_up_interval_days=prediction.recommendation.follow_up_interval_days,
            referral_required=prediction.recommendation.referral_required
        )
    

    # ----------- Build response --------------------------------------------
    
    return PredictionResponse(
        prediction_id=prediction.prediction_id,
        visit_id=prediction.visit_id,
        patient_id=prediction.visit.patient_id if prediction.visit else None,
        diabetes=DiabetesPrediction(
            probability=prediction.diabetes_probability,
            risk_class=prediction.diabetes_risk_class,
            risk_color=get_risk_color(prediction.diabetes_risk_class),
            class_label=prediction.diabetes_class
        ),
        obesity=ObesityPrediction(
            bmi=prediction.visit.screening_data.bmi if prediction.visit and prediction.visit.screening_data else 0,
            bmi_category=prediction.visit.screening_data.bmi_category if prediction.visit and prediction.visit.screening_data else "Unknown",
            risk_class=prediction.obesity_risk_class,
            risk_color=get_risk_color(prediction.obesity_risk_class),
            obesity_class=prediction.obesity_class
        ),
        model_version=prediction.model_version,
        prediction_date=prediction.prediction_date,
        latency_ms=prediction.latency_ms,
        shap_explanation=shap_explanation_response,
        lime_explanation=lime_explanation_response,
        global_feature_importance=global_importance_response,
        recommendation=recommendation_response
    )

# ------ GET /predictions/{prediction_id}/explanations ----------------------------

@router.get(
    "/{prediction_id}/explanations",
    response_model=CombinedExplanationResponse,
    summary="Get all explanations for a prediction",
    description="Get SHAP, LIME, and Global Feature Importance for a specific prediction.",
)
async def get_prediction_explanations(
    prediction_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> CombinedExplanationResponse:
    """
    Get all explanations for a specific prediction.
    
    - Returns SHAP explanation (local, per-patient)
    - Returns LIME explanation (local, model-agnostic)
    - Returns Global Feature Importance (global, model-specific)
    - Requires authentication
    """
    service = PredictionService(db)
    
    # Get prediction with details
    prediction = await service.prediction_repo.get_prediction_with_details(prediction_id)
    if not prediction:
        raise NotFoundError("Prediction", prediction_id)
    
    shap_response = None
    lime_response = None
    global_response = None
    
    # 1. Get SHAP explanation
    shap_explanation = await service.prediction_repo.shap_repo.get_by_id(
        prediction_id=prediction_id,
        id_column="prediction_id"
    )
    
    if shap_explanation and shap_explanation.method == "SHAP":
        # Build feature contributions
        feature_contributions = []
        for feature_name, shap_value in shap_explanation.feature_contributions.items():
            feature_contributions.append(
                FeatureContribution(
                    feature_name=feature_name,
                    value=0.0,  # Will be populated from screening data
                    shap_value=shap_value,
                    impact_direction="Positive" if shap_value > 0 else "Negative",
                    importance_abs=abs(shap_value)
                )
            )
        
        feature_contributions.sort(key=lambda x: x.importance_abs, reverse=True)
        top_positive = [f for f in feature_contributions if f.impact_direction == "Positive"][:5]
        top_negative = [f for f in feature_contributions if f.impact_direction == "Negative"][:5]
        
        shap_response = SHAPExplanationResponse(
            explanation_id=shap_explanation.explanation_id,
            prediction_id=prediction_id,
            base_value=shap_explanation.base_value,
            final_probability=prediction.diabetes_probability,
            feature_contributions=feature_contributions,
            top_positive_features=top_positive,
            top_negative_features=top_negative
        )
    
    # 2. Get LIME explanation
    if shap_explanation and shap_explanation.method == "LIME":
        # Similar to SHAP but without base_value
        feature_contributions = []
        for feature_name, lime_value in shap_explanation.feature_contributions.items():
            feature_contributions.append(
                FeatureContribution(
                    feature_name=feature_name,
                    value=0.0,
                    shap_value=lime_value,
                    impact_direction="Positive" if lime_value > 0 else "Negative",
                    importance_abs=abs(lime_value)
                )
            )
        
        feature_contributions.sort(key=lambda x: x.importance_abs, reverse=True)
        top_positive = [f for f in feature_contributions if f.impact_direction == "Positive"][:5]
        top_negative = [f for f in feature_contributions if f.impact_direction == "Negative"][:5]
        
        lime_response = LIMEExplanationResponse(
            explanation_id=shap_explanation.explanation_id,
            prediction_id=prediction_id,
            feature_contributions=feature_contributions,
            top_positive_features=top_positive,
            top_negative_features=top_negative
        )
    
    # 3. Get Global Feature Importance
    try:
        global_data = await service._get_global_feature_importance_response()
        if global_data:
            global_response = global_data
    except Exception as e:
        logger.warning(f"Failed to get global feature importance: {str(e)}")
    
    return CombinedExplanationResponse(
        prediction_id=prediction_id,
        shap=shap_response,
        lime=lime_response,
        global_feature_importance=global_response
    )

# ----------- GET /predictions/{prediction_id}/recommendation -------------------------

@router.get(
    "/{prediction_id}/recommendation",
    response_model=RecommendationResponse,
    summary="Get recommendation for a prediction",
    description="Get the clinical recommendation for a specific prediction.",
)
async def get_prediction_recommendation(
    prediction_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> RecommendationResponse:
    """
    Get the clinical recommendation for a specific prediction.
    
    - Returns priority, action text, patient advice
    - Includes follow-up interval and referral information
    - Requires authentication
    """
    service = PredictionService(db)
    
    # Get prediction with recommendation
    prediction = await service.prediction_repo.get_prediction_with_details(prediction_id)
    if not prediction:
        raise NotFoundError("Prediction", prediction_id)
    
    if not prediction.recommendation:
        raise NotFoundError("Recommendation", prediction_id)
    
    recommendation = prediction.recommendation
    
    return RecommendationResponse(
        recommendation_id=recommendation.recommendation_id,
        prediction_id=recommendation.prediction_id,
        priority=recommendation.priority,
        action_text=recommendation.action_text,
        patient_advice=recommendation.patient_advice,
        follow_up_interval_days=recommendation.follow_up_interval_days,
        referral_required=recommendation.referral_required
    )


# ---- GET /predictions/patients/{patient_id}/history -------------------------------

@router.get(
    "/patients/{patient_id}/history",
    response_model=list,
    summary="Get prediction history",
    description="Get prediction history for a patient.",
)
async def get_prediction_history(
    patient_id: str,
    limit: int = Query(default=10, ge=1, le=50, description="Max predictions"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> list:
    """
    Get prediction history for a patient.
    
    - Returns chronological list
    - Limited to `limit` results
    - Most recent first
    """
    service = PredictionService(db)
    
    history = await service.prediction_repo.get_prediction_history(
        patient_id=patient_id,
        limit=limit
    )
    
    return history