"""
Clinical notes endpoints.
Handles creation, retrieval, and management of clinical notes.
"""

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user_id, get_client_ip, get_request_metadata
from app.core.logging import get_logger
from app.schemas.clinical_note import (
    ClinicalNoteCreateRequest,
    ClinicalNoteUpdateRequest,
    ClinicalNoteResponse,
    ClinicalNoteListResponse,
)
from app.schemas.common import PaginatedResponse, PaginationParams, SuccessResponse
from app.services.clinical_note_service import ClinicalNoteService
from app.core.exceptions import NotFoundError, InputValidationError, AuthorizationError

logger = get_logger(__name__)
router = APIRouter()


@router.post(
    "/",
    response_model=ClinicalNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create clinical note",
    description="Create a new clinical note for a patient.",
)
async def create_note(
    request: ClinicalNoteCreateRequest,
    patient_id: str = Query(..., description="Patient identifier"),
    visit_id: str = Query(None, description="Associated screening visit"),
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
    metadata: dict = Depends(get_request_metadata),
) -> ClinicalNoteResponse:
    """
    Create a clinical note.
    
    - Links to patient
    - Optionally links to screening visit
    - Records author information
    - Supports urgency flags
    """
    service = ClinicalNoteService(db)
    
    try:
        result = await service.create_note(
            patient_id=patient_id,
            request=request,
            author_id=current_user,
            visit_id=visit_id,
            ip_address=client_ip,
            request_id=metadata.get("request_id")
        )
        
        logger.info(f"Clinical note created: {result.note_id} for patient {patient_id}")
        return result
        
    except NotFoundError as e:
        logger.warning(f"Note creation failed - patient not found: {patient_id}")
        raise
    except InputValidationError as e:
        logger.warning(f"Note validation failed: {str(e)}")
        raise


@router.get(
    "/urgent",
    response_model=PaginatedResponse[ClinicalNoteResponse],
    summary="Get urgent notes",
    description="Get all urgent clinical notes across the system.",
)
async def get_urgent_notes(
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[ClinicalNoteResponse]:
    """
    Get all urgent notes.

    - Notes with YES or CRITICAL urgency
    - System-wide view
    """
    service = ClinicalNoteService(db)

    notes, total = await service.get_urgent_notes(
        page=page,
        page_size=page_size
    )

    return PaginatedResponse.create(notes, total, PaginationParams(page=page, page_size=page_size))


@router.get(
    "/{note_id}",
    response_model=ClinicalNoteResponse,
    summary="Get clinical note",
    description="Get a specific clinical note by ID.",
)
async def get_note(
    note_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
) -> ClinicalNoteResponse:
    """
    Get a clinical note.

    - Returns full note content
    - Includes author and patient info
    """
    service = ClinicalNoteService(db)

    try:
        return await service.get_note(
            note_id=note_id,
            worker_id=current_user
        )
    except NotFoundError as e:
        logger.warning(f"Note not found: {note_id}")
        raise


@router.get(
    "/patients/{patient_id}",
    response_model=PaginatedResponse[ClinicalNoteResponse],
    summary="Get patient notes",
    description="Get all clinical notes for a patient.",
)
async def get_patient_notes(
    patient_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[ClinicalNoteResponse]:
    """
    Get all notes for a patient.

    - Paginated results
    - Most recent first
    - Includes author names
    """
    service = ClinicalNoteService(db)

    pagination = PaginationParams(page=page, page_size=page_size)

    notes, total = await service.get_patient_notes(
        patient_id=patient_id,
        page=page,
        page_size=page_size,
        include_author=True
    )

    return PaginatedResponse.create(notes, total, pagination)



@router.get(
    "/authors/{author_id}",
    response_model=PaginatedResponse[ClinicalNoteResponse],
    summary="Get notes by author",
    description="Get all clinical notes written by a specific author.",
)
async def get_notes_by_author(
    author_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginatedResponse[ClinicalNoteResponse]:
    """
    Get notes by author.
    
    - Returns all notes by a specific healthcare worker
    - Useful for auditing and review
    """
    service = ClinicalNoteService(db)
    
    notes, total = await service.get_notes_by_author(
        author_id=author_id,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse.create(notes, total, PaginationParams(page=page, page_size=page_size))


@router.patch(
    "/{note_id}",
    response_model=ClinicalNoteResponse,
    summary="Update clinical note",
    description="Update an existing clinical note.",
)
async def update_note(
    note_id: str,
    request: ClinicalNoteUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
) -> ClinicalNoteResponse:
    """
    Update a clinical note.
    
    - Only the author can update
    - Partial updates supported
    - Logs update for audit
    """
    service = ClinicalNoteService(db)
    
    try:
        return await service.update_note(
            note_id=note_id,
            request=request,
            worker_id=current_user,
            ip_address=client_ip
        )
    except NotFoundError as e:
        logger.warning(f"Note update failed - not found: {note_id}")
        raise
    except AuthorizationError as e:
        logger.warning(f"Note update failed - unauthorized: {note_id}")
        raise


@router.delete(
    "/{note_id}",
    response_model=SuccessResponse,
    summary="Delete clinical note",
    description="Delete a clinical note (author only).",
)
async def delete_note(
    note_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: str = Depends(get_current_user_id),
    client_ip: str = Depends(get_client_ip),
) -> SuccessResponse:
    """
    Delete a clinical note.
    
    - Only the author can delete
    - Permanent deletion
    - Logs deletion for audit
    """
    service = ClinicalNoteService(db)
    
    try:
        deleted = await service.delete_note(
            note_id=note_id,
            worker_id=current_user,
            ip_address=client_ip
        )
        
        if deleted:
            logger.info(f"Note deleted: {note_id} by worker {current_user}")
            return SuccessResponse(
                success=True,
                message="Note deleted successfully"
            )
        else:
            raise NotFoundError("ClinicalNote", note_id)
            
    except AuthorizationError as e:
        logger.warning(f"Note deletion failed - unauthorized: {note_id}")
        raise