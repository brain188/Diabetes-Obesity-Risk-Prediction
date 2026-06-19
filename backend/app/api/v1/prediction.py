"""
Risk prediction endpoints.
Handles diabetes and obesity risk prediction.
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user_id, get_client_ip, get_request_metadata
from app.core.logging import get_logger
from app.schemas.prediction import PredictionResponse, PredictionRequest
from app.schemas.prediction import DiabetesPrediction, ObesityPrediction
from app.schemas.common import SuccessResponse
from app.services.prediction_service import PredictionService
from app.services.screening_service import ScreeningService
from app.core.exceptions import PredictionError, InputValidationError, NotFoundError, ModelNotLoadedError

logger = get_logger(__name__)
router = APIRouter()


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
            from app.services.patient_service import PatientService
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


@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get prediction result",
    description="Get a specific prediction result by ID.",
)
async def get_prediction(
    prediction_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> PredictionResponse:
    """
    Get a specific prediction.
    
    - Returns prediction with all details
    - Includes diabetes and obesity results
    - Requires authentication
    """
    service = PredictionService(db)
    
    # Get prediction from repository
    prediction = await service.prediction_repo.get_prediction_with_details(prediction_id)
    
    if not prediction:
        raise NotFoundError("Prediction", prediction_id)
    
    # Build response
    from app.core.constants import get_risk_color
    
    return PredictionResponse(
        prediction_id=prediction.prediction_id,
        visit_id=prediction.visit_id,
        patient_id=prediction.visit.patient_id,
        diabetes=DiabetesPrediction(
            probability=prediction.diabetes_probability,
            risk_class=prediction.diabetes_risk_class,
            risk_color=get_risk_color(prediction.diabetes_risk_class),
            class_label=prediction.diabetes_class
        ),
        obesity=ObesityPrediction(
            bmi=prediction.visit.screening_data.bmi,
            bmi_category=prediction.visit.screening_data.bmi_category,
            risk_class=prediction.obesity_risk_class,
            risk_color=get_risk_color(prediction.obesity_risk_class),
            obesity_class=prediction.obesity_class
        ),
        model_version=prediction.model_version,
        prediction_date=prediction.prediction_date,
        latency_ms=prediction.latency_ms
    )


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