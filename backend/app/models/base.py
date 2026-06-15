"""
Base model class with common fields and utilities.
"""

from datetime import datetime
from typing import Any, Dict
from uuid import uuid4

from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """
    pass


class TimestampMixin:
    """
    Mixin that adds created_at and updated_at timestamps to models.
    Automatically updates updated_at on record changes.
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated"
    )


def generate_uuid() -> str:
    """Generate a UUID string for primary keys."""
    return str(uuid4())


def to_dict(self, exclude: set = None) -> Dict[str, Any]:
    """
    Convert model instance to dictionary.
    
    Args:
        exclude: Set of field names to exclude
        
    Returns:
        Dictionary representation of the model
    """
    exclude = exclude or set()
    result = {}
    
    for column in self.__table__.columns:
        if column.name not in exclude:
            value = getattr(self, column.name)
            # Handle UUID conversion
            if hasattr(value, 'hex'):
                value = str(value)
            # Handle datetime conversion
            elif isinstance(value, datetime):
                value = value.isoformat()
            result[column.name] = value
    
    return result


# Attach to_dict method to Base
Base.to_dict = to_dict