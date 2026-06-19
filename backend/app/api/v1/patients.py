"""
Patient management endpoints.
Follows REST API design with proper resource naming and pagination.
"""

from typing import Optional

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user_id, get_client_ip, get_request_metadata
from app.core.logging import get_logger
from app.schemas.common import PaginatedResponse, PaginationParams, SuccessResponse
from app.schemas.patient import (
    PatientCreateRequest,
    PatientUpdateRequest,
    PatientResponse,
    PatientListResponse,
    PatientSearchRequest,
)
from app.services.patient_service import PatientService
from app.core.exceptions import NotFoundError, DuplicateError, InputValidationError

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
    description="Create a new patient record with demographic information.",
)
async def create_patient(
    request: PatientCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
    metadata: dict = Depends(get_request_metadata),
) -> PatientResponse:
    """
    Register a new patient.
    
    - Creates patient record
    - Links to current healthcare worker
    - Validates patient age (must be >= 18)
    - Returns patient information
    """
    service = PatientService(db)
    
    try:
        result = await service.register_patient(
            request=request,
            worker_id=current_user,
            ip_address=client_ip,
            request_id=metadata.get("request_id")
        )
        
        logger.info(f"Patient created: {result.patient_id} by worker {current_user}")
        return result
        
    except DuplicateError as e:
        logger.warning(f"Patient creation failed: {str(e)}")
        raise
    except InputValidationError as e:
        logger.warning(f"Patient validation failed: {str(e)}")
        raise


@router.get(
    "/",
    response_model=PaginatedResponse[PatientListResponse],
    summary="List patients",
    description="Get paginated list of patients.",
)
async def list_patients(
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[PatientListResponse]:
    """
    List all patients.
    
    - Paginated results
    - Sorted by creation date
    - Returns patient summaries
    """
    service = PatientService(db)
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    patients, total = await service.patient_repo.get_patients_by_worker(
        worker_id=current_user,
        skip=pagination.offset,
        limit=pagination.limit
    )
    
    # Convert to response format with last visit date
    items = []
    for patient in patients:
        # Get last visit date
        from app.services.screening_service import ScreeningService
        screening_service = ScreeningService(db)
        latest_visit = await screening_service.screening_repo.get_latest_visit(patient.patient_id)
        
        items.append(
            PatientListResponse(
                patient_id=patient.patient_id,
                full_name=patient.full_name,
                age=patient.age,
                sex=patient.sex,
                last_visit_date=latest_visit.visit_date if latest_visit else None
            )
        )
    
    
    return PaginatedResponse.create(items, total, pagination)


@router.get(
    "/search",
    response_model=PaginatedResponse[PatientListResponse],
    summary="Search patients",
    description="Search patients by name or patient ID.",
)
async def search_patients(
    query: str = Query(..., min_length=2, description="Search query"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[PatientListResponse]:
    """
    Search for patients.
    
    - Searches by name or patient ID
    - Paginated results
    - Returns matching patients
    """
    service = PatientService(db)
    
    pagination = PaginationParams(page=page, page_size=page_size)
    
    patients, total = await service.search_patients(
        query=query,
        worker_id=current_user,
        page=page,
        page_size=page_size
    )
    
    items = [
        PatientListResponse(
            patient_id=p.patient_id,
            full_name=p.full_name,
            age=p.age,
            sex=p.sex,
            last_visit_date=None
        )
        for p in patients
    ]
    
    return PaginatedResponse.create(items, total, pagination)


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Get patient by ID",
    description="Get complete patient information by ID.",
)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> PatientResponse:
    """
    Get a specific patient.
    
    - Returns full patient details
    - Includes all demographic information
    """
    service = PatientService(db)
    
    try:
        return await service.get_patient(
            patient_id=patient_id,
            worker_id=current_user
        )
    except NotFoundError as e:
        logger.warning(f"Patient not found: {patient_id}")
        raise


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update patient",
    description="Update patient information (partial update).",
)
async def update_patient(
    patient_id: str,
    request: PatientUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
) -> PatientResponse:
    """
    Update a patient.
    
    - Partial updates supported
    - Validates input data
    - Logs update for audit
    """
    service = PatientService(db)
    
    try:
        return await service.update_patient(
            patient_id=patient_id,
            request=request,
            worker_id=current_user,
            ip_address=client_ip
        )
    except NotFoundError as e:
        logger.warning(f"Patient update failed - not found: {patient_id}")
        raise
    except DuplicateError as e:
        logger.warning(f"Patient update failed - duplicate: {str(e)}")
        raise


@router.delete(
    "/{patient_id}",
    response_model=SuccessResponse,
    summary="Delete patient",
    description="Soft delete a patient (deactivate record).",
)
async def delete_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
) -> SuccessResponse:
    """
    Delete a patient (soft delete).
    
    - Soft delete (mark as inactive)
    - Logs deletion for audit
    - Requires authentication
    """
    service = PatientService(db)
    
    try:
        deleted = await service.soft_delete_patient(
            patient_id=patient_id,
            worker_id=current_user,
            ip_address=client_ip
        )
        
        if deleted:
            return SuccessResponse(
                success=True,
                message="Patient deleted successfully"
            )
        else:
            raise NotFoundError("Patient", patient_id)
            
    except NotFoundError as e:
        logger.warning(f"Patient deletion failed - not found: {patient_id}")
        raise


@router.post(
    "/{patient_id}/restore",
    response_model=SuccessResponse,
    summary="Restore patient",
    description="Restore a soft-deleted patient.",
)
async def restore_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
) -> SuccessResponse:
    """
    Restore a soft-deleted patient.
    
    - Reactivates the patient
    - Logs restoration for audit
    - Requires authentication
    """
    service = PatientService(db)
    
    try:
        restored = await service.restore_patient(
            patient_id=patient_id,
            worker_id=current_user,
            ip_address=client_ip
        )
        
        if restored:
            return SuccessResponse(
                success=True,
                message="Patient restored successfully"
            )
        else:
            raise NotFoundError("Patient", patient_id)
            
    except NotFoundError as e:
        logger.warning(f"Patient restoration failed - not found: {patient_id}")
        raise
    except InputValidationError as e:
        logger.warning(f"Patient restoration failed: {str(e)}")
        raise


@router.get(
    "/{patient_id}/summary",
    response_model=dict,
    summary="Get patient summary",
    description="Get patient summary with visit statistics.",
)
async def get_patient_summary(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> dict:
    """
    Get patient summary.
    
    - Includes visit statistics
    - Shows last visit date
    - Total visits count
    """
    service = PatientService(db)
    
    try:
        return await service.get_patient_summary(patient_id)
    except NotFoundError as e:
        logger.warning(f"Patient summary failed - not found: {patient_id}")
        raise