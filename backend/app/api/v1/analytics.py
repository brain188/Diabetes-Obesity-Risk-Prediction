"""
Analytics and feature importance endpoints.
Provides insights into model behavior and global feature importance.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db_session
from app.core.dependencies import get_current_user_id
from app.core.logging import get_logger
from app.models.screening_data import ScreeningData
from app.schemas.shap import GlobalFeatureImportanceResponse
from app.schemas.common import SuccessResponse
from app.services.prediction_service import PredictionService
from app.services.audit_service import AuditService
from app.core.exceptions import NotFoundError
from app.models import Patient, ScreeningVisit, Prediction

logger = get_logger(__name__)
router = APIRouter()


@router.get(
    "/feature-importance",
    response_model=GlobalFeatureImportanceResponse,
    summary="Get global feature importance",
    description="Get global feature importance for the diabetes prediction model.",
)
async def get_feature_importance(
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> GlobalFeatureImportanceResponse:
    """
    Get global feature importance.
    
    - Shows which features most influence predictions
    - Same for all patients (global view)
    - Cached for performance
    """
    service = PredictionService(db)
    
    importance_data = await service.get_global_feature_importance()
    
    return GlobalFeatureImportanceResponse(
        model_version=importance_data.get("model_version", "unknown"),
        feature_importance={
            item["feature"]: item["importance"]
            for item in importance_data.get("importance", [])
        },
        sorted_features=[
            item["feature"]
            for item in importance_data.get("importance", [])
        ],
        updated_at=importance_data.get("updated_at", "")
    )


@router.get(
    "/audit/summary",
    response_model=dict,
    summary="Get audit summary",
    description="Get system audit summary statistics.",
)
async def get_audit_summary(
    days: int = Query(default=7, ge=1, le=90, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> dict:
    """
    Get audit summary.
    
    - Returns event counts by type
    - Shows failed login attempts
    - Aggregated statistics
    """
    service = AuditService(db)
    
    summary = await service.get_system_audit_summary(days=days)
    return summary


@router.get(
    "/audit/activities",
    response_model=list,
    summary="Get recent activities",
    description="Get recent system activities.",
)
async def get_recent_activities(
    limit: int = Query(default=50, ge=1, le=200, description="Max activities"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> list:
    """
    Get recent system activities.
    
    - Returns recent audit logs
    - Useful for monitoring
    """
    service = AuditService(db)
    
    activities = await service.get_recent_activities(limit=limit)
    return activities


@router.get(
    "/audit/user/{worker_id}",
    response_model=dict,
    summary="Get user audit trail",
    description="Get audit trail for a specific user.",
)
async def get_user_audit_trail(
    worker_id: str,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> dict:
    """
    Get audit trail for a specific user.
    
    - Paginated results
    - Shows all actions by a user
    - Useful for auditing
    """
    service = AuditService(db)
    
    audit_trail = await service.get_user_audit_trail(
        worker_id=worker_id,
        page=page,
        page_size=page_size
    )
    
    return audit_trail


@router.get(
    "/model/info",
    response_model=dict,
    summary="Get model information",
    description="Get information about the current ML model.",
)
async def get_model_info(
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> dict:
    """
    Get model information.
    
    - Returns model version
    - Feature names
    - Performance metrics
    """
    from app.ml.model_loader import model_loader
    
    metadata = model_loader.get_metadata()
    
    return {
        "model_name": metadata.get("model_name", "Unknown"),
        "model_version": metadata.get("model_version", "Unknown"),
        "feature_names": metadata.get("feature_names", []),
        "n_features": len(metadata.get("feature_names", [])),
        "test_metrics": metadata.get("test_metrics", {}),
        "thresholds": metadata.get("threshold", {}),
        "target_encoding": metadata.get("target_encoding", {}),
        "is_loaded": model_loader.is_loaded
    }


@router.get(
    "/stats/dashboard",
    response_model=dict,
    summary="Get dashboard statistics",
    description="Get aggregated statistics for the dashboard.",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> dict:
    """
    Get dashboard statistics.
    
    - Total patients
    - Total screenings
    - Risk distributions
    - Recent activity counts
    """
    # Get total patients
    patient_count_stmt = select(func.count()).select_from(Patient)
    patient_count_result = await db.execute(patient_count_stmt)
    total_patients = patient_count_result.scalar() or 0
    
    # Get total screenings
    screening_count_stmt = select(func.count()).select_from(ScreeningVisit)
    screening_count_result = await db.execute(screening_count_stmt)
    total_screenings = screening_count_result.scalar() or 0
    
    # Get risk distributions for diabetes
    diabetes_risk_stmt = select(
        Prediction.diabetes_risk_class,
        func.count(Prediction.prediction_id)
    ).group_by(Prediction.diabetes_risk_class)
    diabetes_risk_result = await db.execute(diabetes_risk_stmt)
    diabetes_risk_counts = {row[0]: row[1] for row in diabetes_risk_result.all()}
    
    # Get risk distributions for obesity
    obesity_risk_stmt = select(
        Prediction.obesity_risk_class,
        func.count(Prediction.prediction_id)
    ).group_by(Prediction.obesity_risk_class)
    obesity_risk_result = await db.execute(obesity_risk_stmt)
    obesity_risk_counts = {row[0]: row[1] for row in obesity_risk_result.all()}
    
    # Get recent activities (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_stmt = select(func.count()).select_from(ScreeningVisit).where(
        ScreeningVisit.created_at >= yesterday
    )
    recent_result = await db.execute(recent_stmt)
    recent_activities = recent_result.scalar() or 0
    
    # Get patients by sex (optional)
    sex_stmt = select(
        Patient.sex,
        func.count(Patient.patient_id)
    ).group_by(Patient.sex)
    sex_result = await db.execute(sex_stmt)
    sex_distribution = {row[0]: row[1] for row in sex_result.all()}
    
    # Get BMI distribution (optional)
    bmi_stmt = select(
        func.avg(ScreeningData.bmi),
        func.min(ScreeningData.bmi),
        func.max(ScreeningData.bmi)
    ).select_from(ScreeningData)
    bmi_result = await db.execute(bmi_stmt)
    bmi_stats = bmi_result.first()
    
    return {
        "total_patients": total_patients,
        "total_screenings": total_screenings,
        "risk_distribution": {
            "diabetes": {
                "Low": diabetes_risk_counts.get("Low", 0),
                "Moderate": diabetes_risk_counts.get("Moderate", 0),
                "High": diabetes_risk_counts.get("High", 0)
            },
            "obesity": {
                "Low": obesity_risk_counts.get("Low", 0),
                "Moderate": obesity_risk_counts.get("Moderate", 0),
                "High": obesity_risk_counts.get("High", 0)
            }
        },
        "sex_distribution": sex_distribution,
        "bmi_stats": {
            "average": round(bmi_stats[0], 2) if bmi_stats and bmi_stats[0] else 0,
            "min": round(bmi_stats[1], 2) if bmi_stats and bmi_stats[1] else 0,
            "max": round(bmi_stats[2], 2) if bmi_stats and bmi_stats[2] else 0
        } if bmi_stats else {},
        "recent_activities": recent_activities,
        "last_updated": datetime.now(timezone.utc).isoformat()
    
    }