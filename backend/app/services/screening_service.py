"""
Screening data capture business logic.
Handles screening visits and data validation.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple, List

from app.core.exceptions import NotFoundError, InputValidationError
from app.repositories.screening_repository import ScreeningRepository
from app.repositories.patient_repository import PatientRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.screening import ScreeningDataRequest, ScreeningDataResponse

logger = logging.getLogger(__name__)


class ScreeningService:
    """Service for screening-related business logic."""
    
    def __init__(self, session):
        """
        Initialize screening service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.screening_repo = ScreeningRepository(session)
        self.patient_repo = PatientRepository(session)
        self.audit_repo = AuditLogRepository(session)
    
    async def create_screening_visit(
        self,
        patient_id: str,
        worker_id: str,
        notes: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> dict:
        """
        Create a new screening visit for a patient.
        
        Args:
            patient_id: Patient identifier
            worker_id: Healthcare worker conducting screening
            notes: Optional visit notes
            ip_address: Client IP for audit
            
        Returns:
            Visit information dictionary
        """
        # Verify patient exists
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise NotFoundError("Patient", patient_id)
        
        # Create visit
        visit = await self.screening_repo.create_visit(
            patient_id=patient_id,
            notes=notes
        )
        
        # Log screening start
        await self.audit_repo.log_event(
            event_type="SCREENING_STARTED",
            action=f"Screening visit started for patient {patient_id}",
            worker_id=worker_id,
            resource_type="ScreeningVisit",
            resource_id=visit.visit_id,
            ip_address=ip_address,
            status="SUCCESS"
        )
        
        logger.info(f"Screening visit created: {visit.visit_id} for patient {patient_id}")
        
        return {
            "visit_id": visit.visit_id,
            "patient_id": patient_id,
            "patient_name": patient.full_name,
            "visit_date": visit.visit_date,
            "notes": notes
        }
    
    async def save_screening_data(
        self,
        visit_id: str,
        request: ScreeningDataRequest,
        worker_id: str,
        ip_address: Optional[str] = None
    ) -> ScreeningDataResponse:
        """
        Save screening data for a visit.
        
        Args:
            visit_id: Screening visit identifier
            request: Screening data request
            worker_id: Healthcare worker saving data
            ip_address: Client IP for audit
            
        Returns:
            Saved screening data response
        """
        # Verify visit exists and get patient age
        visit = await self.screening_repo.get_visit_with_data(visit_id)
        if not visit:
            raise NotFoundError("ScreeningVisit", visit_id)
        
        # Get patient age
        patient = await self.patient_repo.get_by_id(visit.patient_id)
        if not patient:
            raise NotFoundError("Patient", visit.patient_id)
        
        age = patient.age
        if not age:
            raise InputValidationError("Unable to calculate patient age")
        
        # Validate screening data
        self._validate_screening_data(request, age)
        
        # Calculate BMI and category
        bmi = request.weight / (request.height ** 2)
        bmi = round(bmi, 2)
        
        # Determine BMI category
        if bmi < 25:
            bmi_category = "Normal"
        elif bmi < 30:
            bmi_category = "Overweight"
        elif bmi < 35:
            bmi_category = "Obese I"
        else:
            bmi_category = "Obese II+"
        
        # Save screening data
        screening_data = await self.screening_repo.save_screening_data(
            visit_id=visit_id,
            age=age,
            weight=request.weight,
            height=request.height,
            bmi=bmi,
            bmi_category=bmi_category,
            physical_activity=request.physical_activity,
            family_history_diabetes=request.family_history_diabetes,
            previous_gdm=request.previous_gdm,
            has_hypertension=request.has_hypertension,
            is_pregnant=request.is_pregnant,
            residence=request.residence.capitalize()
        )
        
        # Update visit notes if provided
        if request.notes:
            await self.screening_repo.update_visit_notes(visit_id, request.notes)
        
        # Log screening data saved
        await self.audit_repo.log_event(
            event_type="SCREENING_DONE",
            action=f"Screening data saved for visit {visit_id}",
            worker_id=worker_id,
            resource_type="ScreeningVisit",
            resource_id=visit_id,
            ip_address=ip_address,
            details={
                "bmi": bmi,
                "bmi_category": bmi_category,
                "age": age
            }
        )
        
        logger.info(f"Screening data saved for visit: {visit_id}")
        
        return ScreeningDataResponse(
            visit_id=visit_id,
            weight=request.weight,
            height=request.height,
            bmi=bmi,
            bmi_category=bmi_category,
            physical_activity=request.physical_activity,
            family_history_diabetes=request.family_history_diabetes,
            previous_gdm=request.previous_gdm,
            has_hypertension=request.has_hypertension,
            is_pregnant=request.is_pregnant,
            residence=request.residence.capitalize(),
            age=age,
            created_at=screening_data.created_at
        )
    
    def _validate_screening_data(self, request: ScreeningDataRequest, age: int) -> None:
        """
        Validate screening data business rules.
        
        Args:
            request: Screening data request
            age: Patient age
            
        Raises:
            ValidationError: If validation fails
        """
        # Check if female for GDM questions
        # Note: sex would need to be passed in or retrieved
        pass  # This will be implemented with patient sex check
    
    async def get_visit_with_data(
        self,
        visit_id: str,
        include_patient: bool = True
    ) -> dict:
        """
        Get screening visit with its data.
        
        Args:
            visit_id: Visit identifier
            include_patient: Whether to include patient info
            
        Returns:
            Visit with data dictionary
        """
        visit = await self.screening_repo.get_visit_with_data_or_fail(
            visit_id, 
            include_patient=include_patient
        )
        
        result = {
            "visit_id": visit.visit_id,
            "visit_date": visit.visit_date,
            "notes": visit.notes,
            "created_at": visit.created_at
        }
        
        if visit.screening_data:
            result["screening_data"] = ScreeningDataResponse(
                visit_id=visit.visit_id,
                weight=visit.screening_data.weight,
                height=visit.screening_data.height,
                bmi=visit.screening_data.bmi,
                bmi_category=visit.screening_data.bmi_category,
                physical_activity=visit.screening_data.physical_activity,
                family_history_diabetes=visit.screening_data.family_history_diabetes,
                previous_gdm=visit.screening_data.previous_gdm,
                has_hypertension=visit.screening_data.has_hypertension,
                is_pregnant=visit.screening_data.is_pregnant,
                residence=visit.screening_data.residence,
                age=visit.screening_data.age,
                created_at=visit.screening_data.created_at
            )
        
        if include_patient and visit.patient:
            result["patient"] = {
                "patient_id": visit.patient.patient_id,
                "full_name": visit.patient.full_name,
                "age": visit.patient.age
            }
        
        return result
    
    async def get_patient_visits(
        self,
        patient_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[dict], int]:
        """
        Get all screening visits for a patient.
        
        Args:
            patient_id: Patient identifier
            page: Page number
            page_size: Items per page
            
        Returns:
            Tuple of (visits list, total count)
        """
        offset = (page - 1) * page_size
        
        visits, total = await self.screening_repo.get_patient_visits(
            patient_id=patient_id,
            skip=offset,
            limit=page_size,
            include_predictions=True
        )
        
        visit_responses = []
        for visit in visits:
            visit_dict = {
                "visit_id": visit.visit_id,
                "visit_date": visit.visit_date,
                "notes": visit.notes
            }
            
            if visit.screening_data:
                visit_dict["bmi"] = visit.screening_data.bmi
                visit_dict["bmi_category"] = visit.screening_data.bmi_category
            
            if visit.prediction:
                visit_dict["diabetes_risk"] = visit.prediction.diabetes_risk_class
                visit_dict["obesity_risk"] = visit.prediction.obesity_risk_class
            
            visit_responses.append(visit_dict)
        
        return visit_responses, total
    
    async def get_latest_screening_data(self, patient_id: str) -> Optional[dict]:
        """
        Get the most recent screening data for a patient.
        
        Args:
            patient_id: Patient identifier
            
        Returns:
            Latest screening data or None
        """
        latest_visit = await self.screening_repo.get_latest_visit(patient_id)
        
        if not latest_visit or not latest_visit.screening_data:
            return None
        
        return {
            "visit_id": latest_visit.visit_id,
            "visit_date": latest_visit.visit_date,
            "bmi": latest_visit.screening_data.bmi,
            "bmi_category": latest_visit.screening_data.bmi_category,
            "physical_activity": latest_visit.screening_data.physical_activity,
            "family_history_diabetes": latest_visit.screening_data.family_history_diabetes,
            "has_hypertension": latest_visit.screening_data.has_hypertension,
            "residence": latest_visit.screening_data.residence
        }