"""
Audit logging business logic.
Handles systematic logging of all security-relevant events.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from app.repositories.audit_log_repository import AuditLogRepository
from app.core.constants import (
    AUDIT_LOGIN, AUDIT_LOGOUT, AUDIT_PREDICTION_RUN,
    AUDIT_REPORT_GENERATED, AUDIT_PATIENT_CREATED,
    AUDIT_SCREENING_DONE, AUDIT_PASSWORD_RESET
)

logger = logging.getLogger(__name__)


class AuditService:
    """Service for audit logging business logic."""
    
    def __init__(self, session):
        """
        Initialize audit service with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.audit_repo = AuditLogRepository(session)
    
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
    ) -> None:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event
            action: Description of action
            worker_id: Worker identifier (if applicable)
            resource_type: Type of resource accessed
            resource_id: Resource identifier
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request correlation ID
            status: SUCCESS or FAILED
            error_message: Error message if failed
            details: Additional event details
        """
        await self.audit_repo.log_event(
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
            details=details
        )
    
    async def log_user_activity(
        self,
        worker_id: str,
        activity_type: str,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log general user activity.
        
        Args:
            worker_id: Worker identifier
            activity_type: Type of activity
            ip_address: Client IP address
            details: Additional activity details
        """
        await self.audit_repo.log_event(
            event_type="USER_ACTIVITY",
            action=activity_type,
            worker_id=worker_id,
            ip_address=ip_address,
            details=details
        )
    
    async def get_user_audit_trail(
        self,
        worker_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        Get audit trail for a specific user.
        
        Args:
            worker_id: Worker identifier
            start_date: Optional start date
            end_date: Optional end date
            page: Page number
            page_size: Items per page
            
        Returns:
            Paginated audit trail
        """
        offset = (page - 1) * page_size
        
        logs = await self.audit_repo.get_user_audit_trail(
            worker_id=worker_id,
            start_date=start_date,
            end_date=end_date,
            skip=offset,
            limit=page_size
        )
        
        # Count total (simplified - in production use a count query)
        total = len(logs)
        
        return {
            "items": [
                {
                    "log_id": log.log_id,
                    "event_type": log.event_type,
                    "action": log.action,
                    "resource_type": log.resource_type,
                    "resource_id": log.resource_id,
                    "ip_address": log.ip_address,
                    "status": log.status,
                    "created_at": log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 1
        }
    
    async def get_system_audit_summary(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Get summary of system audit events.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Dictionary with audit summary statistics
        """
        start_date = datetime.now(datetime.timezone.utc) - timedelta(days=days)
        
        # Get events by type
        event_counts = {}
        event_types = [
            AUDIT_LOGIN, AUDIT_LOGOUT, AUDIT_PREDICTION_RUN,
            AUDIT_REPORT_GENERATED, AUDIT_PATIENT_CREATED,
            AUDIT_SCREENING_DONE, AUDIT_PASSWORD_RESET
        ]
        
        for event_type in event_types:
            logs = await self.audit_repo.get_events_by_type(
                event_type=event_type,
                start_date=start_date,
                limit=1000
            )
            event_counts[event_type] = len(logs)
        
        # Get failed login attempts
        failed_logins = await self.audit_repo.get_events_by_type(
            event_type=AUDIT_LOGIN,
            start_date=start_date,
            limit=1000
        )
        failed_login_count = len([l for l in failed_logins if l.status == "FAILED"])
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.now(datetime.timezone.utc).isoformat(),
            "event_counts": event_counts,
            "failed_logins": failed_login_count,
            "total_events": sum(event_counts.values())
        }
    
    async def get_recent_activities(
        self,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get recent system activities.
        
        Args:
            limit: Maximum number of activities
            
        Returns:
            List of recent activities
        """
        logs = await self.audit_repo.get_recent_activities(limit=limit)
        
        return [
            {
                "log_id": log.log_id,
                "event_type": log.event_type,
                "action": log.action,
                "worker_id": log.worker_id,
                "ip_address": log.ip_address,
                "status": log.status,
                "timestamp": log.created_at.isoformat() if log.created_at else None
            }
            for log in logs
        ]
    
    async def check_suspicious_activity(
        self,
        worker_id: str,
        time_window_minutes: int = 15,
        max_attempts: int = 5
    ) -> bool:
        """
        Check for suspicious activity patterns.
        
        Args:
            worker_id: Worker identifier
            time_window_minutes: Time window to check
            max_attempts: Maximum allowed attempts
            
        Returns:
            True if suspicious activity detected
        """
        start_time = datetime.now(datetime.timezone.utc) - timedelta(minutes=time_window_minutes)
        
        # Get recent login attempts
        logs = await self.audit_repo.get_user_audit_trail(
            worker_id=worker_id,
            start_date=start_time,
            limit=100
        )
        
        # Count failed login attempts
        failed_attempts = len([
            log for log in logs 
            if log.event_type == AUDIT_LOGIN and log.status == "FAILED"
        ])
        
        if failed_attempts >= max_attempts:
            logger.warning(f"Suspicious activity detected for user {worker_id}: "
                          f"{failed_attempts} failed login attempts in {time_window_minutes} minutes")
            return True
        
        return False