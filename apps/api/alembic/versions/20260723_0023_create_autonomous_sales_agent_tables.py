"""Create autonomous sales agent tables.

Revision ID: 20260723_0023
Revises: 20260723_0022
Create Date: 2026-07-23 22:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260723_0023"
down_revision: str | None = "20260723_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base() -> list[sa.Column[object]]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _json() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def upgrade() -> None:
    op.create_table(
        "autonomous_sales_agent_runs",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("stage", sa.String(64), nullable=False),
        sa.Column("next_action", sa.String(64), nullable=False, server_default="wait"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="asa-v1"),
        sa.Column("metadata_json", _json(), nullable=False),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_autonomous_sales_agent_runs_company_id_companies"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autonomous_sales_agent_runs")),
    )
    op.create_index("ix_asa_runs_company_created", "autonomous_sales_agent_runs", ["company_id", "created_at"])
    op.create_index("ix_asa_runs_stage", "autonomous_sales_agent_runs", ["stage"])

    op.create_table(
        "asa_workflow_transitions",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("from_stage", sa.String(64), nullable=True),
        sa.Column("to_stage", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("actor", sa.String(128), nullable=False, server_default="system"),
        sa.Column("next_action", sa.String(128), nullable=False, server_default="continue"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_asa_workflow_transitions_company_id_companies"),
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["autonomous_sales_agent_runs.id"],
            name=op.f("fk_asa_workflow_transitions_run_id_autonomous_sales_agent_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asa_workflow_transitions")),
    )
    op.create_index("ix_asa_transitions_company_ts", "asa_workflow_transitions", ["company_id", "occurred_at"])
    op.create_index("ix_asa_transitions_stage", "asa_workflow_transitions", ["to_stage"])

    op.create_table(
        "asa_timeline_events",
        *_base(),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False, server_default=""),
        sa.Column("actor", sa.String(128), nullable=False, server_default="system"),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence", _json(), nullable=False),
        sa.Column("immutable", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.ForeignKeyConstraint(
            ["company_id"],
            ["companies.id"],
            name=op.f("fk_asa_timeline_events_company_id_companies"),
        ),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["autonomous_sales_agent_runs.id"],
            name=op.f("fk_asa_timeline_events_run_id_autonomous_sales_agent_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asa_timeline_events")),
    )
    op.create_index("ix_asa_timeline_company_occurred", "asa_timeline_events", ["company_id", "occurred_at"])

    op.create_table(
        "asa_work_queue_snapshots",
        *_base(),
        sa.Column("kind", sa.String(32), nullable=False, server_default="work_queue"),
        sa.Column("payload", _json(), nullable=False),
        sa.Column("item_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("revenue_forecast", sa.Float(), nullable=False, server_default="0"),
        sa.Column("scoring_version", sa.String(64), nullable=False, server_default="asa-v1"),
        sa.Column("evidence_chain", _json(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_asa_work_queue_snapshots")),
    )
    op.create_index("ix_asa_wq_created", "asa_work_queue_snapshots", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_asa_wq_created", table_name="asa_work_queue_snapshots")
    op.drop_table("asa_work_queue_snapshots")
    op.drop_index("ix_asa_timeline_company_occurred", table_name="asa_timeline_events")
    op.drop_table("asa_timeline_events")
    op.drop_index("ix_asa_transitions_stage", table_name="asa_workflow_transitions")
    op.drop_index("ix_asa_transitions_company_ts", table_name="asa_workflow_transitions")
    op.drop_table("asa_workflow_transitions")
    op.drop_index("ix_asa_runs_stage", table_name="autonomous_sales_agent_runs")
    op.drop_index("ix_asa_runs_company_created", table_name="autonomous_sales_agent_runs")
    op.drop_table("autonomous_sales_agent_runs")
