"""
Add refresh token fields to healthcare_workers table.

Revision ID: 2024_06_18_0003
Revises: 2024_01_15_0002
Create Date: 2024-06-18 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2024_06_18_0003'
down_revision: Union[str, None] = '2024_01_15_0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add refresh token fields."""
    # Add refresh_token column
    op.add_column(
        'healthcare_workers',
        sa.Column(
            'refresh_token',
            sa.String(255),
            nullable=True,
            unique=True,
            comment='Current valid refresh token (hashed)'
        )
    )
    
    # Add refresh_token_expires column
    op.add_column(
        'healthcare_workers',
        sa.Column(
            'refresh_token_expires',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='Expiration time for refresh token'
        )
    )
    
    # Create index for refresh_token
    op.create_index('idx_hw_refresh_token', 'healthcare_workers', ['refresh_token'])


def downgrade() -> None:
    """Remove refresh token fields."""
    op.drop_index('idx_hw_refresh_token', table_name='healthcare_workers')
    op.drop_column('healthcare_workers', 'refresh_token_expires')
    op.drop_column('healthcare_workers', 'refresh_token')