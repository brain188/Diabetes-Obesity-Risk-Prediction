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
from app.models.report import Report

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

    try:
        importance_data = await service.get_global_feature_importance()
    except Exception as e:
        logger.warning(f"Feature importance unavailable: {str(e)}")
        return GlobalFeatureImportanceResponse(
            model_version="unavailable",
            feature_importance={},
            sorted_features=[],
            updated_at=""
        )

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
    "/risk-distribution",
    response_model=dict,
    summary="Get risk distribution",
    description="Get diabetes and obesity risk distribution across all predictions.",
)
async def get_risk_distribution(
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> dict:
    """Get risk distribution for diabetes and obesity."""
    from app.models import Prediction

    diabetes_stmt = select(
        Prediction.diabetes_risk_class,
        func.count(Prediction.prediction_id)
    ).group_by(Prediction.diabetes_risk_class)
    obesity_stmt = select(
        Prediction.obesity_risk_class,
        func.count(Prediction.prediction_id)
    ).group_by(Prediction.obesity_risk_class)

    d_result = await db.execute(diabetes_stmt)
    o_result = await db.execute(obesity_stmt)
    d_counts = {row[0]: row[1] for row in d_result.all() if row[0]}
    o_counts = {row[0]: row[1] for row in o_result.all() if row[0]}

    return {
        "distribution": {
            "diabetes": {
                "Low": d_counts.get("Low", 0),
                "Moderate": d_counts.get("Moderate", 0),
                "High": d_counts.get("High", 0),
            },
            "obesity": {
                "Low": o_counts.get("Low", 0),
                "Moderate": o_counts.get("Moderate", 0),
                "High": o_counts.get("High", 0),
            },
        }
    }


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
    yesterday = datetime.utcnow() - timedelta(days=1)

    total_patients_r     = await db.execute(select(func.count()).select_from(Patient))
    active_patients_r    = await db.execute(select(func.count()).select_from(Patient).where(Patient.is_active == True))
    total_screenings_r   = await db.execute(select(func.count()).select_from(ScreeningVisit))
    total_predictions_r  = await db.execute(select(func.count()).select_from(Prediction))
    total_reports_r      = await db.execute(select(func.count()).select_from(Report))
    diabetes_risk_r      = await db.execute(select(Prediction.diabetes_risk_class, func.count(Prediction.prediction_id)).group_by(Prediction.diabetes_risk_class))
    obesity_risk_r       = await db.execute(select(Prediction.obesity_risk_class, func.count(Prediction.prediction_id)).group_by(Prediction.obesity_risk_class))
    recent_r             = await db.execute(select(func.count()).select_from(ScreeningVisit).where(ScreeningVisit.created_at >= yesterday))
    sex_r                = await db.execute(select(Patient.sex, func.count(Patient.patient_id)).group_by(Patient.sex))
    bmi_r                = await db.execute(select(func.avg(ScreeningData.bmi), func.min(ScreeningData.bmi), func.max(ScreeningData.bmi)).select_from(ScreeningData))

    total_patients = total_patients_r.scalar() or 0
    active_patients = active_patients_r.scalar() or 0
    total_screenings = total_screenings_r.scalar() or 0
    total_predictions = total_predictions_r.scalar() or 0
    total_reports = total_reports_r.scalar() or 0
    diabetes_risk_counts = {row[0]: row[1] for row in diabetes_risk_r.all() if row[0]}
    obesity_risk_counts = {row[0]: row[1] for row in obesity_risk_r.all() if row[0]}
    recent_activities = recent_r.scalar() or 0
    sex_distribution = {row[0]: row[1] for row in sex_r.all()}
    bmi_stats = bmi_r.first()

    return {
        "total_patients": total_patients,
        "active_patients": active_patients,
        "total_screenings": total_screenings,
        "total_predictions": total_predictions,
        "total_reports": total_reports,
        "high_risk_count": diabetes_risk_counts.get("High", 0),
        "moderate_risk_count": diabetes_risk_counts.get("Moderate", 0),
        "low_risk_count": diabetes_risk_counts.get("Low", 0),
        "risk_distribution": {
            "diabetes": {
                "Low": diabetes_risk_counts.get("Low", 0),
                "Moderate": diabetes_risk_counts.get("Moderate", 0),
                "High": diabetes_risk_counts.get("High", 0),
            },
            "obesity": {
                "Low": obesity_risk_counts.get("Low", 0),
                "Moderate": obesity_risk_counts.get("Moderate", 0),
                "High": obesity_risk_counts.get("High", 0),
            },
        },
        "sex_distribution": sex_distribution,
        "bmi_stats": {
            "average": round(bmi_stats[0], 2) if bmi_stats and bmi_stats[0] else 0,
            "min": round(bmi_stats[1], 2) if bmi_stats and bmi_stats[1] else 0,
            "max": round(bmi_stats[2], 2) if bmi_stats and bmi_stats[2] else 0,
        } if bmi_stats else {},
        "recent_activities": recent_activities,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/stats/trends",
    response_model=list,
    summary="Get monthly trends",
    description="Get monthly screening and prediction counts for the last N months.",
)
async def get_monthly_trends(
    months: int = Query(default=6, ge=1, le=24),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> list:
    """Monthly screening and prediction volume for trend chart."""
    now = datetime.now(timezone.utc)
    result = []
    for i in range(months - 1, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=30 * i)).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if i > 0:
            month_end = (now.replace(day=1) - timedelta(days=30 * (i - 1))).replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            month_end = now

        screening_stmt = select(func.count()).select_from(ScreeningVisit).where(
            and_(ScreeningVisit.created_at >= month_start, ScreeningVisit.created_at < month_end)
        )
        prediction_stmt = select(func.count()).select_from(Prediction).where(
            and_(Prediction.prediction_date >= month_start, Prediction.prediction_date < month_end)
        )
        s_result = await db.execute(screening_stmt)
        p_result = await db.execute(prediction_stmt)

        result.append({
            "month": month_start.strftime("%b %Y"),
            "screenings": s_result.scalar() or 0,
            "predictions": p_result.scalar() or 0,
        })
    return result