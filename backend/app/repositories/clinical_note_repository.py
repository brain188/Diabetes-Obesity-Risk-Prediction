"""
Repository for ClinicalNote model operations.
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.clinical_note import ClinicalNote
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ClinicalNoteRepository(BaseRepository[ClinicalNote]):
    """Repository for clinical note operations."""
    
    def __init__(self, session):
        super().__init__(ClinicalNote, session)
    
    async def create_note(
        self,
        patient_id: str,
        content: str,
        author_id: str,
        title: Optional[str] = None,
        visit_id: Optional[str] = None,
        note_type: str = "GENERAL",
        is_urgent: str = "NO"
    ) -> ClinicalNote:
        """
        Create a new clinical note.
        
        Args:
            patient_id: Patient identifier
            content: Note content
            author_id: Healthcare worker who wrote the note
            title: Optional note title
            visit_id: Optional associated screening visit
            note_type: Type of note (GENERAL/FOLLOW_UP/REFERRAL)
            is_urgent: Urgency flag (NO/YES/CRITICAL)
            
        Returns:
            Created ClinicalNote instance
        """
        note = await self.create(
            patient_id=patient_id,
            content=content,
            author_id=author_id,
            title=title,
            visit_id=visit_id,
            note_type=note_type,
            is_urgent=is_urgent
        )
        
        logger.info(f"Created clinical note {note.note_id} for patient {patient_id}")
        return note
    
    async def get_patient_notes(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        include_author: bool = True
    ) -> Tuple[List[ClinicalNote], int]:
        """
        Get all clinical notes for a patient.
        
        Args:
            patient_id: Patient identifier
            skip: Number of records to skip
            limit: Maximum records to return
            include_author: Whether to load author data
            
        Returns:
            Tuple of (notes list, total count)
        """
        try:
            # Build query
            stmt = select(ClinicalNote).where(ClinicalNote.patient_id == patient_id)
            
            if include_author:
                stmt = stmt.options(selectinload(ClinicalNote.author))
            
            # Get total count
            count_stmt = select(func.count()).select_from(ClinicalNote).where(
                ClinicalNote.patient_id == patient_id
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0
            
            # Get paginated results
            stmt = stmt.order_by(desc(ClinicalNote.created_at)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            notes = list(result.scalars().all())
            
            return notes, total
        except Exception as e:
            logger.error(f"Failed to get notes for patient {patient_id}: {str(e)}")
            raise
    
    async def get_urgent_notes(
        self,
        skip: int = 0,
        limit: int = 50
    ) -> List[ClinicalNote]:
        """
        Get all urgent clinical notes.
        
        Args:
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of urgent ClinicalNote instances
        """
        try:
            stmt = select(ClinicalNote).where(
                ClinicalNote.is_urgent.in_(["YES", "CRITICAL"])
            ).order_by(
                desc(ClinicalNote.is_urgent),
                desc(ClinicalNote.created_at)
            ).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get urgent notes: {str(e)}")
            raise
    
    async def get_notes_by_author(
        self,
        author_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[ClinicalNote], int]:
        """
        Get clinical notes written by a specific author.
        
        Args:
            author_id: Author identifier
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (notes list, total count)
        """
        try:
            # Get total count
            total = await self.count(author_id=author_id)
            
            # Get paginated results
            stmt = select(ClinicalNote).where(
                ClinicalNote.author_id == author_id
            ).order_by(desc(ClinicalNote.created_at)).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            notes = list(result.scalars().all())
            
            return notes, total
        except Exception as e:
            logger.error(f"Failed to get notes for author {author_id}: {str(e)}")
            raise
    
    async def get_notes_by_visit(
        self,
        visit_id: str
    ) -> Optional[ClinicalNote]:
        """
        Get clinical note associated with a specific visit.
        
        Args:
            visit_id: Screening visit identifier
            
        Returns:
            ClinicalNote instance or None
        """
        try:
            stmt = select(ClinicalNote).where(ClinicalNote.visit_id == visit_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get note for visit {visit_id}: {str(e)}")
            raise
    
    async def update_note(
        self,
        note_id: str,
        **kwargs
    ) -> ClinicalNote:
        """
        Update a clinical note.
        
        Args:
            note_id: Note identifier
            **kwargs: Fields to update
            
        Returns:
            Updated ClinicalNote instance
        """
        # Don't allow updating certain fields
        forbidden_fields = {"note_id", "patient_id", "author_id", "created_at"}
        update_data = {k: v for k, v in kwargs.items() if k not in forbidden_fields and v is not None}
        
        if not update_data:
            return await self.get_by_id_or_fail(note_id)
        
        note = await self.update(note_id, **update_data)
        logger.info(f"Updated clinical note {note_id}")
        return note