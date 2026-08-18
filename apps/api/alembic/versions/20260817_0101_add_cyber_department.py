"""Add CYBER to buying_event_department.

Revision ID: 20260817_0101
Revises: a1b2c3d4e5f6
Create Date: 2026-08-17
"""

from alembic import op

revision = "20260817_0101"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE buying_event_department ADD VALUE IF NOT EXISTS 'CYBER'")


def downgrade() -> None:
    # PostgreSQL cannot easily drop enum values; leave CYBER in place.
    pass
