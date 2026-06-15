"""
Repository for Patient model operations.
"""

import logging
from datetime import date
from typing import List, Optional, Tuple

from sqlalchemy import select, or_, func
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
            national_id=national_id
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
        limit: int = 20
    ) -> Tuple[List[Patient], int]:
        """
        Search patients by name or patient ID.
        
        Args:
            query: Search query (name or patient ID)
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (patients list, total count)
        """
        try:
            # Build search condition
            search_term = f"%{query}%"
            stmt = select(Patient).where(
                or_(
                    Patient.full_name.ilike(search_term),
                    Patient.patient_id.ilike(search_term),
                    Patient.national_id.ilike(search_term) if Patient.national_id.isnot(None) else False
                )
            )
            
            # Get total count
            count_stmt = select(func.count()).select_from(Patient).where(
                or_(
                    Patient.full_name.ilike(search_term),
                    Patient.patient_id.ilike(search_term)
                )
            )
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
        include_visits: bool = True
    ) -> Optional[Patient]:
        """
        Get patient with optional eager loading of visits.
        
        Args:
            patient_id: Patient identifier
            include_visits: Whether to load screening visits
            
        Returns:
            Patient instance or None
        """
        try:
            stmt = select(Patient).where(Patient.patient_id == patient_id)
            
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
        limit: int = 20
    ) -> Tuple[List[Patient], int]:
        """
        Get all patients registered by a specific healthcare worker.
        
        Args:
            worker_id: Healthcare worker identifier
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (patients list, total count)
        """
        try:
            # Get total count
            total = await self.count(worker_id=worker_id)
            
            # Get paginated results
            stmt = select(Patient).where(
                Patient.worker_id == worker_id
            ).offset(skip).limit(limit).order_by(Patient.created_at.desc())
            
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
        forbidden_fields = {"patient_id", "worker_id", "created_at"}
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
            "registered_at": patient.created_at
        }