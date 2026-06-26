"""
Repository for Report model operations.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError, DatabaseError
from app.models.report import Report
from app.models.screening_data import ScreeningVisit
from app.models.base import generate_uuid
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
        try:
            # Check if report already exists
            existing = await self.get_report_by_visit(visit_id)
            if existing:
                logger.info(f"Report already exists for visit {visit_id}, updating...")
                return await self.update_report(existing.report_id, file_path, format, file_size_bytes, checksum)
            
            # Create new report with proper types
            report = Report(
                report_id=generate_uuid(),
                visit_id=visit_id,
                format=format.upper(),
                file_path=file_path,
                generated_by=generated_by,
                file_size_bytes=file_size_bytes,
                checksum=checksum,
                generated_at=datetime.now(timezone.utc),
                download_count="0"
            )
            self.session.add(report)
            await self.session.flush()
            await self.session.refresh(report)
            
            logger.info(f"Created report {report.report_id} for visit {visit_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to create report for visit {visit_id}: {str(e)}")
            raise DatabaseError(f"Failed to create report: {str(e)}")
    
    async def update_report(
        self,
        report_id: str,
        file_path: str,
        format: str,
        file_size_bytes: Optional[str] = None,
        checksum: Optional[str] = None
    ) -> Report:
        """Update an existing report."""
        try:
            report = await self.get_by_id_or_fail(report_id)
            report.format = format.upper()
            report.file_path = file_path
            report.file_size_bytes = file_size_bytes
            report.checksum = checksum
            report.generated_at = datetime.now(timezone.utc)
            
            await self.session.flush()
            await self.session.refresh(report)
            
            logger.info(f"Updated report {report_id}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to update report {report_id}: {str(e)}")
            raise DatabaseError(f"Failed to update report: {str(e)}")
    
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
                selectinload(Report.visit).selectinload(ScreeningVisit.patient),
                selectinload(Report.healthcare_worker),
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
        try:
            report = await self.get_by_id_or_fail(report_id)
            
            # Increment download count (convert to int, increment, convert back to string)
            current_count = int(report.download_count) if report.download_count else 0
            new_count = str(current_count + 1)
            
            report.download_count = new_count
            report.downloaded_at = datetime.now(timezone.utc)
            
            await self.session.flush()
            await self.session.refresh(report)
            
            logger.debug(f"Incremented download count for report {report_id} to {new_count}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to increment download count for {report_id}: {str(e)}")
            raise
    
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
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
            
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