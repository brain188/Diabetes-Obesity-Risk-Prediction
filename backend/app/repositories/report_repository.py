"""
Repository for Report model operations.
"""

import logging
from datetime import datetime
from typing import List, Optional, Tuple
from datetime import timedelta

from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.models.report import Report
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ReportRepository(BaseRepository[Report]):
    """Repository for report operations."""
    
    def __init__(self, session):
        super().__init__(Report, session)
    
    async def create_report(
        self,
        visit_id: str,
        format: str,
        file_path: str,
        generated_by: Optional[str] = None,
        file_size_bytes: Optional[str] = None,
        checksum: Optional[str] = None
    ) -> Report:
        """
        Create a new report record.
        
        Args:
            visit_id: Screening visit identifier
            format: Report format (PDF/JSON)
            file_path: Path to stored report file
            generated_by: Healthcare worker who generated the report
            file_size_bytes: Size of the report file
            checksum: SHA-256 checksum for integrity
            
        Returns:
            Created Report instance
        """
        report = await self.create(
            visit_id=visit_id,
            format=format.upper(),
            file_path=file_path,
            generated_by=generated_by,
            file_size_bytes=file_size_bytes,
            checksum=checksum,
            generated_at=datetime.utcnow(),
            download_count=0
        )
        
        logger.info(f"Created report {report.report_id} for visit {visit_id}")
        return report
    
    async def get_report_with_details(
        self,
        report_id: str
    ) -> Optional[Report]:
        """
        Get report with patient and visit details.
        
        Args:
            report_id: Report identifier
            
        Returns:
            Report instance with loaded relationships
        """
        try:
            stmt = select(Report).where(
                Report.report_id == report_id
            ).options(
                selectinload(Report.visit).selectinload(Report.visit.patient),
                selectinload(Report.healthcare_worker)
            )
            
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get report {report_id} with details: {str(e)}")
            raise
    
    async def get_report_by_visit(
        self,
        visit_id: str
    ) -> Optional[Report]:
        """
        Get report by visit ID.
        
        Args:
            visit_id: Screening visit identifier
            
        Returns:
            Report instance or None
        """
        try:
            stmt = select(Report).where(Report.visit_id == visit_id)
            result = await self.session.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get report for visit {visit_id}: {str(e)}")
            raise
    
    async def increment_download_count(
        self,
        report_id: str
    ) -> Report:
        """
        Increment the download counter for a report.
        
        Args:
            report_id: Report identifier
            
        Returns:
            Updated Report instance
        """
        report = await self.get_by_id_or_fail(report_id)
        
        # Increment download count
        current_count = int(report.download_count) if report.download_count else 0
        new_count = str(current_count + 1)
        
        report = await self.update(
            report_id,
            download_count=new_count,
            downloaded_at=datetime.now(datetime.timezone.utc)
        )
        
        logger.debug(f"Incremented download count for report {report_id} to {new_count}")
        return report
    
    async def get_patient_reports(
        self,
        patient_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Report], int]:
        """
        Get all reports for a patient.
        
        Args:
            patient_id: Patient identifier
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            Tuple of (reports list, total count)
        """
        try:
            # Query reports through visits
            stmt = select(Report).join(
                Report.visit
            ).where(
                Report.visit.has(patient_id=patient_id)
            )
            
            # Get total count
            count_stmt = select(func.count()).select_from(Report).join(
                Report.visit
            ).where(
                Report.visit.has(patient_id=patient_id)
            )
            count_result = await self.session.execute(count_stmt)
            total = count_result.scalar() or 0
            
            # Get paginated results
            stmt = stmt.order_by(desc(Report.generated_at)).offset(skip).limit(limit)
            result = await self.session.execute(stmt)
            reports = list(result.scalars().all())
            
            return reports, total
        except Exception as e:
            logger.error(f"Failed to get reports for patient {patient_id}: {str(e)}")
            raise
    
    async def get_reports_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[Report]:
        """
        Get reports generated within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of Report instances
        """
        try:
            stmt = select(Report).where(
                Report.generated_at.between(start_date, end_date)
            ).order_by(desc(Report.generated_at)).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get reports by date range: {str(e)}")
            raise
    
    async def delete_old_reports(
        self,
        older_than_days: int = 30
    ) -> int:
        """
        Delete reports older than specified days.
        
        Args:
            older_than_days: Delete reports older than this many days
            
        Returns:
            Number of reports deleted
        """
        try:
            cutoff_date = datetime.now(datetime.timezone.utc) - timedelta(days=older_than_days)
            
            # First get the reports to delete their files
            stmt = select(Report).where(Report.generated_at < cutoff_date)
            result = await self.session.execute(stmt)
            reports = list(result.scalars().all())
            
            # Delete from database
            for report in reports:
                await self.delete(report.report_id)
            
            logger.info(f"Deleted {len(reports)} reports older than {older_than_days} days")
            return len(reports)
        except Exception as e:
            logger.error(f"Failed to delete old reports: {str(e)}")
            raise
