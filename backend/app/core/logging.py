"""
Logging configuration for the Intelligent DSS application.
Provides structured logging, file rotation, and different log levels.
"""

import logging
import logging.handlers
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.core.config import settings

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)


class RequestLogFilter(logging.Filter):
    """Filter to add request-specific information to log records."""
    
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = '-'
        if not hasattr(record, 'user_id'):
            record.user_id = '-'
        if not hasattr(record, 'client_ip'):
            record.client_ip = '-'
        return True


def setup_logging() -> None:
    """
    Configure logging for the entire application.
    Sets up console and file handlers with appropriate formatters.
    """
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create formatter with more detailed format
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | '
            'req_id=%(request_id)s | user=%(user_id)s | '
            '%(message)s | [%(filename)s:%(lineno)d]',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Simple console formatter for development
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # ========== Root Logger ==========
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplication
    root_logger.handlers.clear()
    
    # ========== Console Handler ==========
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if settings.ENVIRONMENT == "development":
        console_handler.setFormatter(console_formatter)
    else:
        console_handler.setFormatter(detailed_formatter)
    
    root_logger.addHandler(console_handler)
    
    # ========== File Handler (All Logs) ==========
    log_file_path = log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # ========== Error File Handler (Errors Only) ==========
    error_file_path = log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.handlers.RotatingFileHandler(
        error_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # ========== Add Request Filter ==========
    request_filter = RequestLogFilter()
    for handler in root_logger.handlers:
        handler.addFilter(request_filter)
    
    # ========== Reduce Noise from Third-Party Loggers ==========
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("passlib").setLevel(logging.WARNING)
    logging.getLogger("jose").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, Environment: {settings.ENVIRONMENT}")
    logger.info(f"Log files: {log_file_path}, {error_file_path}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class AuditLogger:
    """
    Specialized logger for audit trail events.
    Tracks all security-relevant actions for compliance.
    """
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_login(self, user_id: str, success: bool, ip_address: str, details: str = None):
        """Log authentication attempts."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"AUDIT | LOGIN | User: {user_id} | Status: {status} | IP: {ip_address} | Details: {details}"
        )
    
    def log_logout(self, user_id: str, ip_address: str):
        """Log user logout events."""
        self.logger.info(f"AUDIT | LOGOUT | User: {user_id} | IP: {ip_address}")
    
    def log_data_access(self, user_id: str, action: str, resource_type: str, resource_id: str, ip_address: str):
        """Log data access events (read, write, delete)."""
        self.logger.info(
            f"AUDIT | DATA_ACCESS | User: {user_id} | Action: {action} | "
            f"Resource: {resource_type}:{resource_id} | IP: {ip_address}"
        )
    
    def log_prediction(self, user_id: str, patient_id: str, diabetes_risk: str, obesity_risk: str, ip_address: str):
        """Log risk prediction events."""
        self.logger.info(
            f"AUDIT | PREDICTION | User: {user_id} | Patient: {patient_id} | "
            f"Diabetes: {diabetes_risk} | Obesity: {obesity_risk} | IP: {ip_address}"
        )
    
    def log_report_generation(self, user_id: str, patient_id: str, report_id: str, ip_address: str):
        """Log report generation events."""
        self.logger.info(
            f"AUDIT | REPORT | User: {user_id} | Patient: {patient_id} | "
            f"Report: {report_id} | IP: {ip_address}"
        )
    
    def log_password_reset(self, email: str, success: bool, ip_address: str):
        """Log password reset attempts."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"AUDIT | PASSWORD_RESET | Email: {email} | Status: {status} | IP: {ip_address}"
        )


# Global audit logger instance
audit_logger = AuditLogger()