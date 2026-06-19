"""
Add is_active field to patients table for soft delete.

Revision ID: 2024_01_15_0002
Revises: 2024_01_01_0001
Create Date: 2024-01-15 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2024_01_15_0002'
down_revision: Union[str, None] = '2024_01_01_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_active and deleted_at columns to patients table."""
    # Add is_active column with default True
    op.add_column(
        'patients',
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            server_default='true',
            comment='Soft delete flag: True for active, False for deleted'
        )
    )
    
    # Add deleted_at column
    op.add_column(
        'patients',
        sa.Column(
            'deleted_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Timestamp when patient was soft deleted'
        )
    )
    
    # Create index for is_active
    op.create_index('idx_patient_active', 'patients', ['is_active'])


def downgrade() -> None:
    """Remove is_active and deleted_at columns from patients table."""
    op.drop_index('idx_patient_active', table_name='patients')
    op.drop_column('patients', 'deleted_at')
    op.drop_column('patients', 'is_active')