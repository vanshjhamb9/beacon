"""create_company_universe_table

Revision ID: 07f2c24ee08e
Revises: 115d7a8fbfee
Create Date: 2026-08-09 21:06:37.579324+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '07f2c24ee08e'
down_revision: Union[str, None] = '115d7a8fbfee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create company_universe table
    op.create_table('company_universe',
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=True),
        sa.Column('industry', sa.String(length=128), nullable=True),
        sa.Column('country', sa.String(length=128), nullable=True),
        sa.Column('employees', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=64), nullable=False),
        sa.Column('icp_match_score', sa.Float(), nullable=False),
        sa.Column('has_buying_event', sa.Boolean(), nullable=False),
        sa.Column('buying_event_id', sa.UUID(), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_company_universe'))
    )
    op.create_index(op.f('ix_company_universe_company_name'), 'company_universe', ['company_name'], unique=False)
    op.create_index('ix_company_universe_country', 'company_universe', ['country'], unique=False)
    op.create_index('ix_company_universe_domain', 'company_universe', ['domain'], unique=False)
    op.create_index('ix_company_universe_has_buying_event', 'company_universe', ['has_buying_event'], unique=False)
    op.create_index('ix_company_universe_industry', 'company_universe', ['industry'], unique=False)
    op.create_index('ix_company_universe_source', 'company_universe', ['source'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_company_universe_source', table_name='company_universe')
    op.drop_index('ix_company_universe_industry', table_name='company_universe')
    op.drop_index('ix_company_universe_has_buying_event', table_name='company_universe')
    op.drop_index('ix_company_universe_domain', table_name='company_universe')
    op.drop_index('ix_company_universe_country', table_name='company_universe')
    op.drop_index(op.f('ix_company_universe_company_name'), table_name='company_universe')
    op.drop_table('company_universe')
