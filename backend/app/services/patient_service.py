"""
Patient management business logic.
Handles patient registration, search, and record management.
"""

import logging
from datetime import date
from typing import List, Optional, Tuple

from app.core.exceptions import NotFoundError, InputValidationError
from app.repositories.patient_repository import PatientRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest, PatientResponse

logger = logging.getLogger(__name__)


class PatientService:
    """Service for patient-related business logic."""
    
    def __init__(self, session):
        """
        Initialize patient service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.audit_repo = AuditLogRepository(session)
    
    async def register_patient(
        self,
        request: PatientCreateRequest,
        worker_id: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> PatientResponse:
        """
        Register a new patient.
        
        Args:
            request: Patient creation request
            worker_id: Healthcare worker registering the patient
            ip_address: Client IP for audit
            request_id: Request ID for tracing
            
        Returns:
            Created patient response
        """
        # Validate age
        today = date.today()
        age = today.year - request.date_of_birth.year - (
            (today.month, today.day) < (request.date_of_birth.month, request.date_of_birth.day)
        )
        
        if age < 18:
            raise InputValidationError("Patient must be at least 18 years old")
        
        if age > 120:
            raise InputValidationError("Invalid date of birth")
        
        # Create patient
        patient = await self.patient_repo.create_patient(
            full_name=request.full_name,
            date_of_birth=request.date_of_birth,
            sex=request.sex,
            worker_id=worker_id,
            contact_info=request.contact_info,
            national_id=request.national_id
        )
        
        # Log patient creation
        await self.audit_repo.log_patient_created(
            worker_id=worker_id,
            patient_id=patient.patient_id,
            patient_name=patient.full_name,
            ip_address=ip_address,
            request_id=request_id
        )
        
        logger.info(f"Patient registered: {patient.patient_id} by worker {worker_id}")
        
        return PatientResponse(
            patient_id=patient.patient_id,
            full_name=patient.full_name,
            date_of_birth=patient.date_of_birth,
            age=patient.age,
            sex=patient.sex,
            contact_info=patient.contact_info,
            national_id=patient.national_id,
            worker_id=patient.worker_id,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            is_active=patient.is_active,
        )
    
    async def get_patient(
        self,
        patient_id: str,
        worker_id: Optional[str] = None,
        include_inactive: bool = False
    ) -> PatientResponse:
        """
        Get patient by ID.
        
        Args:
            patient_id: Patient identifier
            worker_id: Optional worker ID for access check
            include_inactive: Whether to include inactive patients
            
        Returns:
            Patient response
            
        Raises:
            NotFoundError: If patient not found
        """
        patient = await self.patient_repo.get_patient_with_visits(
            patient_id=patient_id,
            include_visits=False,
            include_inactive=include_inactive
        )
        
        if not patient:
            raise NotFoundError("Patient", patient_id)
        
        # Log access
        if worker_id:
            await self.audit_repo.log_event(
                event_type="PATIENT_VIEWED",
                action=f"Patient record viewed",
                worker_id=worker_id,
                resource_type="Patient",
                resource_id=patient_id,
                status="SUCCESS"
            )
        
        return PatientResponse(
            patient_id=patient.patient_id,
            full_name=patient.full_name,
            date_of_birth=patient.date_of_birth,
            age=patient.age,
            sex=patient.sex,
            contact_info=patient.contact_info,
            national_id=patient.national_id,
            worker_id=patient.worker_id,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            is_active=patient.is_active
        )
    
    async def search_patients(
        self,
        query: str,
        worker_id: str,
        page: int = 1,
        page_size: int = 20,
        include_inactive: bool = False
    ) -> Tuple[List[PatientResponse], int]:
        """
        Search patients by name or ID.
        
        Args:
            query: Search query
            worker_id: Worker ID for access control
            page: Page number
            page_size: Items per page
            include_inactive: Whether to include inactive patients
            
        Returns:
            Tuple of (patients list, total count)
        """
        offset = (page - 1) * page_size
        
        patients, total = await self.patient_repo.search_patients(
            query=query,
            skip=offset,
            limit=page_size,
            include_inactive=include_inactive
        )
        
        # Convert to response models
        patient_responses = []
        for patient in patients:
            patient_responses.append(PatientResponse(
                patient_id=patient.patient_id,
                full_name=patient.full_name,
                date_of_birth=patient.date_of_birth,
                age=patient.age,
                sex=patient.sex,
                contact_info=patient.contact_info,
                national_id=patient.national_id,
                worker_id=patient.worker_id,
                created_at=patient.created_at,
                updated_at=patient.updated_at,
                is_active=patient.is_active
            ))
        
        return patient_responses, total
    
    async def update_patient(
        self,
        patient_id: str,
        request: PatientUpdateRequest,
        worker_id: str,
        ip_address: Optional[str] = None
    ) -> PatientResponse:
        """
        Update patient information.
        
        Args:
            patient_id: Patient identifier
            request: Update request
            worker_id: Worker making the update
            ip_address: Client IP for audit
            
        Returns:
            Updated patient response
            
        Raises:
            NotFoundError: If patient not found
        """
        # Check if patient exists and is active
        existing = await self.patient_repo.get_patient_with_visits(
            patient_id=patient_id,
            include_visits=False,
            include_inactive=False
        )
        
        if not existing:
            raise NotFoundError("Patient", patient_id)
        
        # Update patient
        update_data = request.model_dump(exclude_unset=True)
        patient = await self.patient_repo.update_patient(patient_id, **update_data)
        
        # Log update
        await self.audit_repo.log_event(
            event_type="PATIENT_UPDATED",
            action=f"Patient record updated",
            worker_id=worker_id,
            resource_type="Patient",
            resource_id=patient_id,
            ip_address=ip_address,
            status="SUCCESS"
        )
        
        logger.info(f"Patient updated: {patient_id} by worker {worker_id}")
        
        return PatientResponse(
            patient_id=patient.patient_id,
            full_name=patient.full_name,
            date_of_birth=patient.date_of_birth,
            age=patient.age,
            sex=patient.sex,
            contact_info=patient.contact_info,
            national_id=patient.national_id,
            worker_id=patient.worker_id,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
            is_active=patient.is_active
        )
    

    async def soft_delete_patient(
        self,
        patient_id: str,
        worker_id: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Soft delete a patient.
        
        Args:
            patient_id: Patient identifier
            worker_id: Worker performing the deletion
            ip_address: Client IP for audit
            
        Returns:
            True if deleted
            
        Raises:
            NotFoundError: If patient not found
        """
        # Check if patient exists and is active
        existing = await self.patient_repo.get_patient_with_visits(
            patient_id=patient_id,
            include_visits=False,
            include_inactive=False
        )
        
        if not existing:
            raise NotFoundError("Patient", patient_id)
        
        # Soft delete
        result = await self.patient_repo.soft_delete_patient(
            patient_id=patient_id,
            worker_id=worker_id
        )
        
        if result:
            # Log deletion
            await self.audit_repo.log_event(
                event_type="PATIENT_DELETED",
                action=f"Patient {patient_id} soft deleted",
                worker_id=worker_id,
                resource_type="Patient",
                resource_id=patient_id,
                ip_address=ip_address,
                status="SUCCESS"
            )
            
            logger.info(f"Patient soft deleted: {patient_id} by worker {worker_id}")
        
        return result
    
    async def restore_patient(
        self,
        patient_id: str,
        worker_id: str,
        ip_address: Optional[str] = None
    ) -> bool:
        """
        Restore a soft-deleted patient.
        
        Args:
            patient_id: Patient identifier
            worker_id: Worker performing the restoration
            ip_address: Client IP for audit
            
        Returns:
            True if restored
            
        Raises:
            NotFoundError: If patient not found
        """
        # Check if patient exists and is inactive
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError("Patient", patient_id)
        
        if patient.is_active:
            raise InputValidationError("Patient is already active")
        
        # Restore
        result = await self.patient_repo.restore_patient(
            patient_id=patient_id,
            worker_id=worker_id
        )
        
        if result:
            # Log restoration
            await self.audit_repo.log_event(
                event_type="PATIENT_RESTORED",
                action=f"Patient {patient_id} restored",
                worker_id=worker_id,
                resource_type="Patient",
                resource_id=patient_id,
                ip_address=ip_address,
                status="SUCCESS"
            )
            
            logger.info(f"Patient restored: {patient_id} by worker {worker_id}")
        
        return result
    

    async def get_patient_summary(self, patient_id: str) -> dict:
        """
        Get patient summary including visit statistics.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Patient summary dictionary
        """
        summary = await self.patient_repo.get_patient_summary(patient_id)
        return summary
    
    async def get_patient_age(self, patient_id: str) -> Optional[int]:
        """
        Get patient's current age.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Age in years or None
        """
        return await self.patient_repo.get_patient_age(patient_id)