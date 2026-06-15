"""
Repository for ScreeningVisit and ScreeningData operations.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.screening_data import ScreeningVisit, ScreeningData
from app.models.patient import Patient
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ScreeningRepository:
    """Repository for screening-related operations."""
    
    def __init__(self, session):
        self.session = session
        self.visit_repo = BaseRepository(ScreeningVisit, session)
        self.data_repo = BaseRepository(ScreeningData, session)
    
    async def create_visit(
        self,
        patient_id: str,
        notes: Optional[str] = None
    ) -> ScreeningVisit:
        """
        Create a new screening visit.
        
        Args:
            patient_id: Patient identifier
            notes: Optional visit notes
            
        Returns:
            Created ScreeningVisit instance
        """
        visit = await self.visit_repo.create(
            patient_id=patient_id,
            notes=notes,
            visit_date=datetime.now(datetime.timezone.utc)
        )
        
        logger.info(f"Created screening visit {visit.visit_id} for patient {patient_id}")
        return visit
    
    async def save_screening_data(
        self,
        visit_id: str,
        age: int,
        **data
    ) -> ScreeningData:
        """
        Save screening data for a visit.
        
        Args:
            visit_id: Screening visit identifier
            age: Patient's age at screening
            **data: Screening measurements
            
        Returns:
            Created ScreeningData instance
        """
        # Calculate BMI if weight and height are provided
        bmi = None
        bmi_category = None
        
        if "weight" in data and "height" in data and data["weight"] and data["height"]:
            bmi = data["weight"] / (data["height"] ** 2)
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
        
        screening_data = await self.data_repo.create(
            visit_id=visit_id,
            bmi=bmi,
            bmi_category=bmi_category,
            age=age,
            **{k: v for k, v in data.items() if v is not None}
        )
        
        logger.info(f"Saved screening data for visit {visit_id}")
        return screening_data
    
    async def get_visit_with_data(
        self,
        visit_id: str,
        include_patient: bool = False
    ) -> Optional[ScreeningVisit]:
        """
        Get screening visit with its data.
        
        Args:
            visit_id: Visit identifier
            include_patient: Whether to include patient data
            
        Returns:
            ScreeningVisit instance or None
        """
        try:
            stmt = select(ScreeningVisit).where(
                ScreeningVisit.visit_id == visit_id
            ).options(selectinload(ScreeningVisit.screening_data))
            
            if include_patient:
                stmt = stmt.options(selectinload(ScreeningVisit.patient))
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get visit {visit_id}: {str(e)}")
            raise
    
    async def get_visit_with_data_or_fail(
        self,
        visit_id: str,
        include_patient: bool = False
    ) -> ScreeningVisit:
        """Get visit with data or raise NotFoundError."""
        visit = await self.get_visit_with_data(visit_id, include_patient)
        if not visit:
            raise NotFoundError("ScreeningVisit", visit_id)
        return visit
    
    async def get_patient_visits(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20,
        include_predictions: bool = False
    ) -> Tuple[List[ScreeningVisit], int]:
        """
        Get all screening visits for a patient.
        
        Args:
            patient_id: Patient identifier
            skip: Number of records to skip
            limit: Maximum records to return
            include_predictions: Whether to load predictions
            
        Returns:
            Tuple of (visits list, total count)
        """
        try:
            # Build query
            stmt = select(ScreeningVisit).where(
                ScreeningVisit.patient_id == patient_id
            )
            
            if include_predictions:
                stmt = stmt.options(selectinload(ScreeningVisit.prediction))
            
            # Get total count
            count_stmt = select(func.count()).select_from(ScreeningVisit).where(
                ScreeningVisit.patient_id == patient_id
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0
            
            # Get paginated results
            stmt = stmt.order_by(desc(ScreeningVisit.visit_date)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            visits = list(result.scalars().all())
            
            return visits, total
        except Exception as e:
            logger.error(f"Failed to get visits for patient {patient_id}: {str(e)}")
            raise
    
    async def get_latest_visit(self, patient_id: str) -> Optional[ScreeningVisit]:
        """Get the most recent screening visit for a patient."""
        try:
            stmt = select(ScreeningVisit).where(
                ScreeningVisit.patient_id == patient_id
            ).order_by(desc(ScreeningVisit.visit_date)).limit(1)
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get latest visit for patient {patient_id}: {str(e)}")
            raise
    
    async def update_visit_notes(self, visit_id: str, notes: str) -> ScreeningVisit:
        """Update notes for a screening visit."""
        visit = await self.visit_repo.update(visit_id, notes=notes)
        logger.info(f"Updated notes for visit {visit_id}")
        return visit
    
    async def get_visits_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[ScreeningVisit]:
        """
        Get visits within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of ScreeningVisit instances
        """
        try:
            stmt = select(ScreeningVisit).where(
                ScreeningVisit.visit_date.between(start_date, end_date)
            ).order_by(ScreeningVisit.visit_date).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get visits by date range: {str(e)}")
            raise