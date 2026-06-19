"""
Screening data endpoints.
Handles screening visits and data capture.
"""

from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user_id, get_client_ip, get_request_metadata
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, SuccessResponse
from app.schemas.screening import (
    ScreeningDataRequest,
    ScreeningDataResponse,
    ScreeningVisitResponse,
    ScreeningVisitListResponse,
)
from app.services.screening_service import ScreeningService
from app.core.exceptions import NotFoundError, InputValidationError

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/visits",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Start screening visit",
    description="Create a new screening visit for a patient.",
)
async def create_visit(
    patient_id: str = Query(..., description="Patient identifier"),
    notes: Optional[str] = Query(None, description="Visit notes"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
) -> dict:
    """
    Start a new screening visit.
    
    - Creates visit record
    - Links to patient
    - Returns visit ID for data entry
    """
    service = ScreeningService(db)
    
    try:
        result = await service.create_screening_visit(
            patient_id=patient_id,
            worker_id=current_user,
            notes=notes,
            ip_address=client_ip
        )
        
        logger.info(f"Screening visit created: {result['visit_id']} for patient {patient_id}")
        return result
        
    except NotFoundError as e:
        logger.warning(f"Visit creation failed - patient not found: {patient_id}")
        raise


@router.post(
    "/visits/{visit_id}/data",
    response_model=ScreeningDataResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save screening data",
    description="Save screening measurements for a visit.",
)
async def save_screening_data(
    visit_id: str,
    request: ScreeningDataRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
    metadata: dict = Depends(get_request_metadata),
) -> ScreeningDataResponse:
    """
    Save screening data.
    
    - Validates all measurements
    - Calculates BMI automatically
    - Links to screening visit
    """
    service = ScreeningService(db)
    
    try:
        result = await service.save_screening_data(
            visit_id=visit_id,
            request=request,
            worker_id=current_user,
            ip_address=client_ip
        )
        
        logger.info(f"Screening data saved for visit: {visit_id}")
        return result
        
    except NotFoundError as e:
        logger.warning(f"Screening data save failed - visit not found: {visit_id}")
        raise
    except InputValidationError as e:
        logger.warning(f"Screening data validation failed: {str(e)}")
        raise


@router.get(
    "/visits/{visit_id}",
    response_model=dict,
    summary="Get screening visit",
    description="Get complete screening visit with data.",
)
async def get_visit(
    visit_id: str,
    include_patient: bool = Query(default=True, description="Include patient info"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> dict:
    """
    Get a screening visit.
    
    - Returns visit details
    - Includes screening data
    - Optionally includes patient info
    """
    service = ScreeningService(db)
    
    try:
        return await service.get_visit_with_data(
            visit_id=visit_id,
            include_patient=include_patient
        )
    except NotFoundError as e:
        logger.warning(f"Visit not found: {visit_id}")
        raise


@router.get(
    "/patients/{patient_id}/visits",
    response_model=PaginatedResponse[dict],
    summary="Get patient visits",
    description="Get all screening visits for a patient.",
)
async def get_patient_visits(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[dict]:
    """
    Get all visits for a patient.
    
    - Paginated results
    - Most recent first
    - Includes prediction results if available
    """
    service = ScreeningService(db)
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    visits, total = await service.get_patient_visits(
        patient_id=patient_id,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse.create(visits, total, pagination)


@router.get(
    "/patients/{patient_id}/latest",
    response_model=Optional[dict],
    summary="Get latest screening data",
    description="Get the most recent screening data for a patient.",
)
async def get_latest_screening(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> Optional[dict]:
    """
    Get latest screening data.
    
    - Returns most recent screening measurements
    - Used for quick patient overview
    """
    service = ScreeningService(db)
    
    return await service.get_latest_screening_data(patient_id)


@router.patch(
    "/visits/{visit_id}/notes",
    response_model=SuccessResponse,
    summary="Update visit notes",
    description="Update notes for a screening visit.",
)
async def update_visit_notes(
    visit_id: str,
    notes: str = Query(..., description="Updated notes"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> SuccessResponse:
    """
    Update visit notes.
    
    - Idempotent operation
    - Updates only the notes field
    """
    service = ScreeningService(db)
    
    try:
        await service.screening_repo.update_visit_notes(visit_id, notes)
        logger.info(f"Updated notes for visit: {visit_id}")
        
        return SuccessResponse(
            success=True,
            message="Visit notes updated successfully"
        )
    except NotFoundError as e:
        logger.warning(f"Visit notes update failed - not found: {visit_id}")
        raise