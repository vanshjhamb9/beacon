"""create_buying_events_table

Revision ID: 115d7a8fbfee
Revises: 0100
Create Date: 2026-08-09 21:04:35.574441+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '115d7a8fbfee'
down_revision: Union[str, None] = '0100'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create buying_events table
    op.create_table('buying_events',
        sa.Column('raw_event_id', sa.UUID(), nullable=False),
        sa.Column('department', sa.Enum('COMAI', 'INOWIX', name='buying_event_department'), nullable=False),
        sa.Column('event_type', sa.String(length=64), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('company_domain', sa.String(length=255), nullable=True),
        sa.Column('contact_info', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('disqualifiers', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.Enum('DETECTED', 'VERIFIED', 'DISQUALIFIED', 'PROCESSED', name='buying_event_status'), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disqualified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disqualification_reason', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_buying_events'))
    )
    op.create_index('ix_buying_events_company_name', 'buying_events', ['company_name'], unique=False)
    op.create_index('ix_buying_events_created_at', 'buying_events', ['created_at'], unique=False)
    op.create_index('ix_buying_events_department_status', 'buying_events', ['department', 'status'], unique=False)
    op.create_index(op.f('ix_buying_events_raw_event_id'), 'buying_events', ['raw_event_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_buying_events_raw_event_id'), table_name='buying_events')
    op.drop_index('ix_buying_events_department_status', table_name='buying_events')
    op.drop_index('ix_buying_events_created_at', table_name='buying_events')
    op.drop_index('ix_buying_events_company_name', table_name='buying_events')
    op.drop_table('buying_events')
    op.execute("DROP TYPE IF EXISTS buying_event_status")
    op.execute("DROP TYPE IF EXISTS buying_event_department")
