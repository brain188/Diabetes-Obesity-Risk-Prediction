"""
Clinical note business logic.
Handles creation, retrieval, and management of clinical notes.
"""

import logging
from typing import List, Optional, Tuple

from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.clinical_note_repository import ClinicalNoteRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.clinical_note import (
    ClinicalNoteCreateRequest,
    ClinicalNoteUpdateRequest,
    ClinicalNoteResponse,
    ClinicalNoteListResponse
)

logger = logging.getLogger(__name__)


class ClinicalNoteService:
    """Service for clinical note business logic."""
    
    def __init__(self, session):
        """
        Initialize clinical note service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.note_repo = ClinicalNoteRepository(session)
        self.patient_repo = PatientRepository(session)
        self.audit_repo = AuditLogRepository(session)
    
    async def create_note(
        self,
        patient_id: str,
        request: ClinicalNoteCreateRequest,
        author_id: str,
        visit_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> ClinicalNoteResponse:
        """
        Create a new clinical note.
        
        Args:
            patient_id: Patient identifier
            request: Note creation request
            author_id: Healthcare worker writing the note
            visit_id: Optional associated screening visit
            ip_address: Client IP for audit
            request_id: Request ID for tracing
            
        Returns:
            Created clinical note response
            
        Raises:
            NotFoundError: If patient not found
        """
        # Verify patient exists
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError("Patient", patient_id)
        
        # Create note
        note = await self.note_repo.create_note(
            patient_id=patient_id,
            content=request.content,
            author_id=author_id,
            title=request.title,
            visit_id=visit_id,
            note_type=request.note_type,
            is_urgent=request.is_urgent
        )
        
        # Log note creation
        await self.audit_repo.log_event(
            event_type="CLINICAL_NOTE_ADDED",
            action=f"Clinical note added for patient {patient_id}",
            worker_id=author_id,
            resource_type="ClinicalNote",
            resource_id=note.note_id,
            ip_address=ip_address,
            request_id=request_id,
            details={
                "note_type": request.note_type,
                "is_urgent": request.is_urgent
            }
        )
        
        logger.info(f"Clinical note created: {note.note_id} for patient {patient_id}")
        
        return ClinicalNoteResponse(
            note_id=note.note_id,
            patient_id=patient_id,
            patient_name=patient.full_name,
            visit_id=visit_id,
            author_id=author_id,
            author_name=None,  # Will be populated if needed
            title=note.title,
            content=note.content,
            note_type=note.note_type,
            is_urgent=note.is_urgent,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
    
    async def get_patient_notes(
        self,
        patient_id: str,
        page: int = 1,
        page_size: int = 20,
        include_author: bool = True
    ) -> Tuple[List[ClinicalNoteResponse], int]:
        """
        Get all clinical notes for a patient.
        
        Args:
            patient_id: Patient identifier
            page: Page number
            page_size: Items per page
            include_author: Whether to include author info
            
        Returns:
            Tuple of (notes list, total count)
        """
        offset = (page - 1) * page_size
        
        notes, total = await self.note_repo.get_patient_notes(
            patient_id=patient_id,
            skip=offset,
            limit=page_size,
            include_author=include_author
        )
        
        note_responses = []
        for note in notes:
            note_responses.append(ClinicalNoteResponse(
                note_id=note.note_id,
                patient_id=patient_id,
                patient_name="",  # Will be filled from patient query if needed
                visit_id=note.visit_id,
                author_id=note.author_id,
                author_name=note.author.full_name if note.author else None,
                title=note.title,
                content=note.content,
                note_type=note.note_type,
                is_urgent=note.is_urgent,
                created_at=note.created_at,
                updated_at=note.updated_at
            ))
        
        return note_responses, total
    
    async def get_note(
        self,
        note_id: str,
        worker_id: Optional[str] = None
    ) -> ClinicalNoteResponse:
        """
        Get a specific clinical note by ID.
        
        Args:
            note_id: Note identifier
            worker_id: Optional worker ID for access logging
            
        Returns:
            Clinical note response
            
        Raises:
            NotFoundError: If note not found
        """
        note = await self.note_repo.get_by_id(note_id)
        if not note:
            raise NotFoundError("ClinicalNote", note_id)
        
        # Get patient info
        patient = await self.patient_repo.get_by_id(note.patient_id)
        patient_name = patient.full_name if patient else "Unknown"
        
        # Log access
        if worker_id:
            await self.audit_repo.log_event(
                event_type="CLINICAL_NOTE_VIEWED",
                action=f"Clinical note viewed",
                worker_id=worker_id,
                resource_type="ClinicalNote",
                resource_id=note_id,
                status="SUCCESS"
            )
        
        return ClinicalNoteResponse(
            note_id=note.note_id,
            patient_id=note.patient_id,
            patient_name=patient_name,
            visit_id=note.visit_id,
            author_id=note.author_id,
            author_name=note.author.full_name if note.author else None,
            title=note.title,
            content=note.content,
            note_type=note.note_type,
            is_urgent=note.is_urgent,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
    
    async def update_note(
        self,
        note_id: str,
        request: ClinicalNoteUpdateRequest,
        worker_id: str,
        ip_address: Optional[str] = None
    ) -> ClinicalNoteResponse:
        """
        Update a clinical note.
        
        Args:
            note_id: Note identifier
            request: Update request
            worker_id: Worker making the update
            ip_address: Client IP for audit
            
        Returns:
            Updated clinical note response
            
        Raises:
            NotFoundError: If note not found
            ValidationError: If note cannot be updated
        """
        # Verify note exists
        existing = await self.note_repo.get_by_id(note_id)
        if not existing:
            raise NotFoundError("ClinicalNote", note_id)
        
        # Check if user is the author (security check)
        if existing.author_id != worker_id:
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError("Only the author can edit this note")
        
        # Update note
        update_data = request.model_dump(exclude_unset=True)
        note = await self.note_repo.update_note(note_id, **update_data)
        
        # Log update
        await self.audit_repo.log_event(
            event_type="CLINICAL_NOTE_UPDATED",
            action=f"Clinical note updated",
            worker_id=worker_id,
            resource_type="ClinicalNote",
            resource_id=note_id,
            ip_address=ip_address,
            status="SUCCESS"
        )
        
        logger.info(f"Clinical note updated: {note_id}")
        
        # Get patient info
        patient = await self.patient_repo.get_by_id(note.patient_id)
        patient_name = patient.full_name if patient else "Unknown"
        
        return ClinicalNoteResponse(
            note_id=note.note_id,
            patient_id=note.patient_id,
            patient_name=patient_name,
            visit_id=note.visit_id,
            author_id=note.author_id,
            author_name=note.author.full_name if note.author else None,
            title=note.title,
            content=note.content,
            note_type=note.note_type,
            is_urgent=note.is_urgent,
            created_at=note.created_at,
            updated_at=note.updated_at
        )
    
    async def delete_note(
        self,
        note_id: str,
        worker_id: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Delete a clinical note.
        
        Args:
            note_id: Note identifier
            worker_id: Worker deleting the note
            ip_address: Client IP for audit
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If note not found
            AuthorizationError: If user is not the author
        """
        # Verify note exists and check authorization
        note = await self.note_repo.get_by_id(note_id)
        if not note:
            raise NotFoundError("ClinicalNote", note_id)
        
        if note.author_id != worker_id:
            from app.core.exceptions import AuthorizationError
            raise AuthorizationError("Only the author can delete this note")
        
        # Delete note
        deleted = await self.note_repo.delete(note_id)
        
        if deleted:
            await self.audit_repo.log_event(
                event_type="CLINICAL_NOTE_DELETED",
                action=f"Clinical note deleted",
                worker_id=worker_id,
                resource_type="ClinicalNote",
                resource_id=note_id,
                ip_address=ip_address,
                status="SUCCESS"
            )
            logger.info(f"Clinical note deleted: {note_id}")
        
        return deleted
    
    async def get_urgent_notes(
        self,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[ClinicalNoteResponse], int]:
        """
        Get all urgent clinical notes.
        
        Args:
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (notes list, total count)
        """
        offset = (page - 1) * page_size
        
        notes = await self.note_repo.get_urgent_notes(
            skip=offset,
            limit=page_size
        )
        
        note_responses = []
        for note in notes:
            patient = await self.patient_repo.get_by_id(note.patient_id)
            patient_name = patient.full_name if patient else "Unknown"
            
            note_responses.append(ClinicalNoteResponse(
                note_id=note.note_id,
                patient_id=note.patient_id,
                patient_name=patient_name,
                visit_id=note.visit_id,
                author_id=note.author_id,
                author_name=note.author.full_name if note.author else None,
                title=note.title,
                content=note.content,
                note_type=note.note_type,
                is_urgent=note.is_urgent,
                created_at=note.created_at,
                updated_at=note.updated_at
            ))
        
        return note_responses, len(notes)
    
    async def get_notes_by_author(
        self,
        author_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ClinicalNoteResponse], int]:
        """
        Get all notes written by a specific author.
        
        Args:
            author_id: Author identifier
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (notes list, total count)
        """
        offset = (page - 1) * page_size
        
        notes, total = await self.note_repo.get_notes_by_author(
            author_id=author_id,
            skip=offset,
            limit=page_size
        )
        
        note_responses = []
        for note in notes:
            patient = await self.patient_repo.get_by_id(note.patient_id)
            patient_name = patient.full_name if patient else "Unknown"
            
            note_responses.append(ClinicalNoteResponse(
                note_id=note.note_id,
                patient_id=note.patient_id,
                patient_name=patient_name,
                visit_id=note.visit_id,
                author_id=note.author_id,
                author_name=note.author.full_name if note.author else None,
                title=note.title,
                content=note.content,
                note_type=note.note_type,
                is_urgent=note.is_urgent,
                created_at=note.created_at,
                updated_at=note.updated_at
            ))
        
        return note_responses, total
    
    async def get_note_by_visit(
        self,
        visit_id: str
    ) -> Optional[ClinicalNoteResponse]:
        """
        Get clinical note associated with a specific visit.
        
        Args:
            visit_id: Screening visit identifier
            
        Returns:
            Clinical note response or None
        """
        note = await self.note_repo.get_notes_by_visit(visit_id)
        
        if not note:
            return None
        
        patient = await self.patient_repo.get_by_id(note.patient_id)
        patient_name = patient.full_name if patient else "Unknown"
        
        return ClinicalNoteResponse(
            note_id=note.note_id,
            patient_id=note.patient_id,
            patient_name=patient_name,
            visit_id=note.visit_id,
            author_id=note.author_id,
            author_name=note.author.full_name if note.author else None,
            title=note.title,
            content=note.content,
            note_type=note.note_type,
            is_urgent=note.is_urgent,
            created_at=note.created_at,
            updated_at=note.updated_at
        )