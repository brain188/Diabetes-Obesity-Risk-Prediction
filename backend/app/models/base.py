"""
Shared mixins applied to ORM models.

TimestampMixin  — adds created_at and updated_at to any table that needs them.
UUIDMixin       — provides a UUID primary key.

Using mixins keeps individual model files clean and avoids repeating
the same column definitions across every table.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TimestampMixin:
    """
    Adds created_at and updated_at columns.
    Both are set automatically by the database server (server_default / onupdate).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


def generate_uuid() -> str:
    """Generate a new UUID4 string. Used as the default for PK columns."""
    return str(uuid.uuid4())