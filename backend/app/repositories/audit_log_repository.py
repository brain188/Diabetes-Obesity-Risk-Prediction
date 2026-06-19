"""
Repository for AuditLog model operations.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4

from sqlalchemy import select, and_, func
from sqlalchemy.sql import Select

from app.core.constants import (
    AUDIT_LOGIN, AUDIT_LOGOUT, AUDIT_PREDICTION_RUN, 
    AUDIT_REPORT_GENERATED, AUDIT_PATIENT_CREATED
)
from app.models.audit_log import AuditLog
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for audit log operations."""
    
    def __init__(self, session):
        super().__init__(AuditLog, session)
    
    async def log_event(
        self,
        event_type: str,
        action: str,
        worker_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (LOGIN, PREDICTION_RUN, etc.)
            action: Detailed action description
            worker_id: Healthcare worker ID (if applicable)
            resource_type: Type of resource accessed
            resource_id: Identifier of the resource
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            status: SUCCESS or FAILED
            error_message: Error message if status is FAILED
            details: Additional JSON details
            
        Returns:
            Created AuditLog instance
        """
        import json
        
        log_entry = await self.create(
            log_id=str(uuid4()),
            event_type=event_type,
            action=action,
            worker_id=worker_id,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            status=status,
            error_message=error_message,
            details=json.dumps(details) if details else None
        )
        
        logger.debug(f"Audit log created: {event_type} by {worker_id or 'system'}")
        return log_entry
    
    async def log_login(
        self,
        user_id: str = None,
        email: str = None,
        success: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        worker_id: Optional[str] = None,
        details: Optional[str] = None
    ) -> AuditLog:
        """Log a login attempt."""
        action = f"Login attempt for user: {email or user_id or 'unknown'}"
        return await self.log_event(
            event_type=AUDIT_LOGIN,
            action=action,
            worker_id=worker_id or user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            status="SUCCESS" if success else "FAILED",
            error_message=None if success else "Invalid credentials",
            details=details or {}
        )
    
    async def log_logout(
        self,
        worker_id: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """Log a logout event."""
        return await self.log_event(
            event_type=AUDIT_LOGOUT,
            action="User logged out",
            worker_id=worker_id,
            ip_address=ip_address,
            request_id=request_id,
            status="SUCCESS"
        )
    
    async def log_prediction(
        self,
        worker_id: str,
        patient_id: str,
        diabetes_risk: str,
        obesity_risk: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """Log a risk prediction event."""
        return await self.log_event(
            event_type=AUDIT_PREDICTION_RUN,
            action=f"Risk prediction for patient {patient_id}",
            worker_id=worker_id,
            resource_type="Patient",
            resource_id=patient_id,
            ip_address=ip_address,
            request_id=request_id,
            details={
                "diabetes_risk": diabetes_risk,
                "obesity_risk": obesity_risk
            }
        )
    
    async def log_report_generated(
        self,
        worker_id: str,
        patient_id: str,
        report_id: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """Log a report generation event."""
        return await self.log_event(
            event_type=AUDIT_REPORT_GENERATED,
            action=f"Report generated for patient {patient_id}",
            worker_id=worker_id,
            resource_type="Report",
            resource_id=report_id,
            ip_address=ip_address,
            request_id=request_id
        )
    
    async def log_patient_created(
        self,
        worker_id: str,
        patient_id: str,
        patient_name: str,
        ip_address: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> AuditLog:
        """Log a patient registration event."""
        return await self.log_event(
            event_type=AUDIT_PATIENT_CREATED,
            action=f"Patient registered: {patient_name}",
            worker_id=worker_id,
            resource_type="Patient",
            resource_id=patient_id,
            ip_address=ip_address,
            request_id=request_id
        )
    
    async def get_user_audit_trail(
        self,
        worker_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit trail for a specific user.
        
        Args:
            worker_id: Healthcare worker ID
            start_date: Optional start date filter
            end_date: Optional end date filter
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of AuditLog entries
        """
        try:
            stmt = select(AuditLog).where(AuditLog.worker_id == worker_id)
            
            if start_date:
                stmt = stmt.where(AuditLog.created_at >= start_date)
            if end_date:
                stmt = stmt.where(AuditLog.created_at <= end_date)
            
            stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get audit trail for user {worker_id}: {str(e)}")
            raise
    
    async def get_events_by_type(
        self,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit events by type.
        
        Args:
            event_type: Type of event to filter
            start_date: Optional start date
            end_date: Optional end date
            skip: Number of records to skip
            limit: Maximum records to return
            
        Returns:
            List of AuditLog entries
        """
        try:
            stmt = select(AuditLog).where(AuditLog.event_type == event_type)
            
            if start_date:
                stmt = stmt.where(AuditLog.created_at >= start_date)
            if end_date:
                stmt = stmt.where(AuditLog.created_at <= end_date)
            
            stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get events by type {event_type}: {str(e)}")
            raise
    
    async def get_recent_activities(
        self,
        limit: int = 50
    ) -> List[AuditLog]:
        """
        Get recent system activities.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List of recent AuditLog entries
        """
        try:
            stmt = select(AuditLog).order_by(
                AuditLog.created_at.desc()
            ).limit(limit)
            
            result = await self.session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Failed to get recent activities: {str(e)}")
            raise