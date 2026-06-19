"""
Repository for Patient model operations.
"""

import logging
from datetime import date, datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, or_, func, and_
from sqlalchemy.orm import selectinload

from app.core.exceptions import DuplicateError, NotFoundError
from app.models.patient import Patient
from app.models.screening_data import ScreeningVisit
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class PatientRepository(BaseRepository[Patient]):
    """Repository for patient operations."""
    
    def __init__(self, session):
        super().__init__(Patient, session)
    
    async def create_patient(
        self,
        full_name: str,
        date_of_birth: date,
        sex: str,
        worker_id: str,
        contact_info: Optional[str] = None,
        national_id: Optional[str] = None
    ) -> Patient:
        """
        Create a new patient record.
        
        Args:
            full_name: Patient's full name
            date_of_birth: Date of birth
            sex: Male/Female
            worker_id: Healthcare worker who registered the patient
            contact_info: Optional contact information
            national_id: Optional national ID/medical record number
            
        Returns:
            Created Patient instance
            
        Raises:
            DuplicateError: If national_id already exists
        """
        # Check if national_id already exists (if provided)
        if national_id:
            existing = await self.get_by_national_id(national_id)
            if existing:
                raise DuplicateError(
                    resource="Patient",
                    field="national_id",
                    value=national_id
                )
        
        patient = await self.create(
            full_name=full_name,
            date_of_birth=date_of_birth,
            sex=sex.capitalize(),
            worker_id=worker_id,
            contact_info=contact_info,
            national_id=national_id,
            is_active=True,  # New patients are active by default
            deleted_at=None
        )
        
        logger.info(f"Created patient: {full_name} (ID: {patient.patient_id})")
        return patient
    
    async def get_by_national_id(self, national_id: str) -> Optional[Patient]:
        """Get patient by national ID."""
        try:
            stmt = select(Patient).where(Patient.national_id == national_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get patient by national_id {national_id}: {str(e)}")
            raise
    
    async def search_patients(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20,
        include_inactive: bool = False
    ) -> Tuple[List[Patient], int]:
        """
        Search patients by name or patient ID.
        
        Args:
            query: Search query (name or patient ID)
            skip: Number of records to skip
            limit: Maximum records to return
            include_inactive: Whether to include inactive patients
            
        Returns:
            Tuple of (patients list, total count)
        """
        try:
            # Build search condition
            search_term = f"%{query}%"
            
            # Base condition
            conditions = [
                Patient.full_name.ilike(search_term),
                Patient.patient_id.ilike(search_term),
                Patient.national_id.ilike(search_term),
            ]
            
            stmt = select(Patient).where(or_(*conditions))
            
            # Filter by active status
            if not include_inactive:
                stmt = stmt.where(Patient.is_active == True)
            
            # Get total count
            count_stmt = select(func.count()).select_from(Patient).where(or_(*conditions))
            if not include_inactive:
                count_stmt = count_stmt.where(Patient.is_active == True)
            
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0
            
            # Get paginated results
            stmt = stmt.offset(skip).limit(limit).order_by(Patient.full_name)
            result = await self.session.execute(stmt)
            patients = list(result.scalars().all())
            
            return patients, total
        except Exception as e:
            logger.error(f"Failed to search patients with query '{query}': {str(e)}")
            raise
    
    
    
    async def get_patient_with_visits(
        self,
        patient_id: str,
        include_visits: bool = True,
        include_inactive: bool = False
    ) -> Optional[Patient]:
        """
        Get patient with optional eager loading of visits.
        
        Args:
            patient_id: Patient identifier
            include_visits: Whether to load screening visits
            include_inactive: Whether to include inactive patients
            
        Returns:
            Patient instance or None
        """
        try:
            stmt = select(Patient).where(Patient.patient_id == patient_id)
            
            if not include_inactive:
                stmt = stmt.where(Patient.is_active == True)
            
            if include_visits:
                stmt = stmt.options(selectinload(Patient.screening_visits))
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get patient {patient_id} with visits: {str(e)}")
            raise
    
    async def get_patients_by_worker(
        self,
        worker_id: str,
        skip: int = 0,
        limit: int = 20,
        include_inactive: bool = False
    ) -> Tuple[List[Patient], int]:
        """
        Get all patients registered by a specific healthcare worker.
        
        Args:
            worker_id: Healthcare worker identifier
            skip: Number of records to skip
            limit: Maximum records to return
            include_inactive: Whether to include inactive patients
            
        Returns:
            Tuple of (patients list, total count)
        """
        try:
            # Build query with active filter
            filters = {"worker_id": worker_id}
            if not include_inactive:
                filters["is_active"] = True
            
            # Get total count
            total = await self.count(**filters)
            
            # Get paginated results
            stmt = select(Patient).where(
                Patient.worker_id == worker_id
            )
            if not include_inactive:
                stmt = stmt.where(Patient.is_active == True)
            stmt = stmt.offset(skip).limit(limit).order_by(Patient.created_at.desc())
            
            result = await self.session.execute(stmt)
            patients = list(result.scalars().all())
            
            return patients, total
        except Exception as e:
            logger.error(f"Failed to get patients for worker {worker_id}: {str(e)}")
            raise
    
    async def update_patient(
        self,
        patient_id: str,
        **kwargs
    ) -> Patient:
        """
        Update patient information.
        
        Args:
            patient_id: Patient identifier
            **kwargs: Fields to update
            
        Returns:
            Updated Patient instance
        """
        # Don't allow updating certain fields
        forbidden_fields = {"patient_id", "worker_id", "created_at", "is_active", "deleted_at"}
        update_data = {k: v for k, v in kwargs.items() if k not in forbidden_fields and v is not None}
        
        if not update_data:
            return await self.get_by_id_or_fail(patient_id)
        
        # If updating national_id, check for duplicates
        if "national_id" in update_data and update_data["national_id"]:
            existing = await self.get_by_national_id(update_data["national_id"])
            if existing and existing.patient_id != patient_id:
                raise DuplicateError(
                    resource="Patient",
                    field="national_id",
                    value=update_data["national_id"]
                )
        
        # Update patient
        patient = await self.update(patient_id, **update_data)
        logger.info(f"Updated patient {patient_id}")
        return patient
    
    async def soft_delete_patient(
        self,
        patient_id: str,
        worker_id: str
    ) -> bool:
        """
        Soft delete a patient (mark as inactive).
        
        Args:
            patient_id: Patient identifier
            worker_id: Healthcare worker performing the deletion
            
        Returns:
            True if deleted, False otherwise
        """
        try:
            stmt = select(Patient).where(
                and_(
                    Patient.patient_id == patient_id,
                    Patient.is_active == True
                )
            )
            result = await self.session.execute(stmt)
            patient = result.scalar_one_or_none()
            
            if not patient:
                return False
            
            # Soft delete
            patient.is_active = False
            patient.deleted_at = datetime.utcnow()
            
            await self.session.flush()
            await self.session.refresh(patient)
            
            logger.info(f"Soft deleted patient {patient_id} by worker {worker_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to soft delete patient {patient_id}: {str(e)}")
            raise
    
    async def restore_patient(
        self,
        patient_id: str,
        worker_id: str
    ) -> bool:
        """
        Restore a soft-deleted patient.
        
        Args:
            patient_id: Patient identifier
            worker_id: Healthcare worker performing the restoration
            
        Returns:
            True if restored, False otherwise
        """
        try:
            stmt = select(Patient).where(
                and_(
                    Patient.patient_id == patient_id,
                    Patient.is_active == False
                )
            )
            result = await self.session.execute(stmt)
            patient = result.scalar_one_or_none()
            
            if not patient:
                return False
            
            # Restore
            patient.is_active = True
            patient.deleted_at = None
            
            await self.session.flush()
            await self.session.refresh(patient)
            
            logger.info(f"Restored patient {patient_id} by worker {worker_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore patient {patient_id}: {str(e)}")
            raise
    
    async def get_active_patients_count(self, worker_id: Optional[str] = None) -> int:
        """
        Get count of active patients.
        
        Args:
            worker_id: Optional worker ID to filter by
            
        Returns:
            Count of active patients
        """
        filters = {"is_active": True}
        if worker_id:
            filters["worker_id"] = worker_id
        return await self.count(**filters)
    
    async def get_deleted_patients_count(self, worker_id: Optional[str] = None) -> int:
        """
        Get count of deleted patients.
        
        Args:
            worker_id: Optional worker ID to filter by
            
        Returns:
            Count of deleted patients
        """
        filters = {"is_active": False}
        if worker_id:
            filters["worker_id"] = worker_id
        return await self.count(**filters)
    
    async def get_patient_age(self, patient_id: str) -> Optional[int]:
        """Get the current age of a patient."""
        patient = await self.get_by_id(patient_id)
        if not patient:
            return None
        return patient.age
    
    async def get_patient_summary(self, patient_id: str) -> dict:
        """
        Get a summary of patient information including visit statistics.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Dictionary with patient summary
        """
        patient = await self.get_patient_with_visits(patient_id, include_visits=True)
        if not patient:
            raise NotFoundError("Patient", patient_id)
        
        # Calculate visit statistics
        total_visits = len(patient.screening_visits) if patient.screening_visits else 0
        last_visit = patient.screening_visits[0].visit_date if patient.screening_visits else None
        
        return {
            "patient_id": patient.patient_id,
            "full_name": patient.full_name,
            "age": patient.age,
            "sex": patient.sex,
            "total_visits": total_visits,
            "last_visit_date": last_visit,
            "registered_at": patient.created_at,
            "is_active": patient.is_active
        }