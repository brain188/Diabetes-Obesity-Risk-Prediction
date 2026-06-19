"""
API module for route handlers.
"""

from app.api.v1 import auth, patients, screening, prediction, reports, notes, analytics

__all__ = [
    "auth",
    "patients",
    "screening",
    "prediction",
    "reports",
    "notes",
    "analytics",
]