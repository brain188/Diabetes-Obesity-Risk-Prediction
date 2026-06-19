"""
API v1 route handlers.
All endpoints are versioned under /api/v1.
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth,
    patients,
    screening,
    prediction,
    reports,
    notes,
    analytics,
)

# Create main router
router = APIRouter()

# Include all sub-routers
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(patients.router, prefix="/patients", tags=["Patients"])
router.include_router(screening.router, prefix="/screening", tags=["Screening"])
router.include_router(prediction.router, prefix="/predictions", tags=["Predictions"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(notes.router, prefix="/notes", tags=["Clinical Notes"])
router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

__all__ = [
    "router",
    "auth",
    "patients",
    "screening",
    "prediction",
    "reports",
    "notes",
    "analytics",
]