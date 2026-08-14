"""Create data acquisition monitoring tables.

Revision ID: 20260719_0010
Revises: 20260719_0009
Create Date: 2026-07-19 02:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0010"
down_revision: str | None = "20260719_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column[object]]:
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
        "collector_runs",
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("collected", sa.Integer(), nullable=False),
        sa.Column("emitted", sa.Integer(), nullable=False),
        sa.Column("duplicates", sa.Integer(), nullable=False),
        sa.Column("rate_limited", sa.Boolean(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("details", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_collector_runs")),
    )
    op.create_index("ix_collector_runs_source_created", "collector_runs", ["source", "created_at"])
    op.create_index("ix_collector_runs_success_created", "collector_runs", ["success", "created_at"])

    op.create_table(
        "connector_alerts",
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("severity", sa.String(32), nullable=False),
        sa.Column("code", sa.String(64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("consecutive_failures", sa.Integer(), nullable=False),
        sa.Column("details", _json(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_connector_alerts")),
    )
    op.create_index("ix_connector_alerts_source_created", "connector_alerts", ["source", "created_at"])
    op.create_index("ix_connector_alerts_open_severity", "connector_alerts", ["resolved_at", "severity"])

    op.create_table(
        "acquisition_daily_reports",
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("new_companies", sa.Integer(), nullable=False),
        sa.Column("new_opportunities", sa.Integer(), nullable=False),
        sa.Column("high_value_opportunities", sa.Integer(), nullable=False),
        sa.Column("signals_collected", sa.Integer(), nullable=False),
        sa.Column("signals_persisted", sa.Integer(), nullable=False),
        sa.Column("duplicate_rate", sa.Float(), nullable=False),
        sa.Column("coverage_growth", sa.Float(), nullable=False),
        sa.Column("missing_data_trends", _json(), nullable=False),
        sa.Column("collector_performance", _json(), nullable=False),
        sa.Column("benchmarks", _json(), nullable=False),
        sa.Column("alerts", _json(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload", _json(), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_acquisition_daily_reports")),
    )
    op.create_index("ix_acquisition_daily_reports_date", "acquisition_daily_reports", ["report_date"])

    op.create_table(
        "connector_benchmark_snapshots",
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("opportunity_yield", sa.Float(), nullable=False),
        sa.Column("high_value_yield", sa.Float(), nullable=False),
        sa.Column("company_discovery_rate", sa.Float(), nullable=False),
        sa.Column("duplicate_rate", sa.Float(), nullable=False),
        sa.Column("failure_rate", sa.Float(), nullable=False),
        sa.Column("average_latency_ms", sa.Float(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["acquisition_daily_reports.id"],
            name=op.f("fk_connector_benchmark_snapshots_report_id_acquisition_daily_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_connector_benchmark_snapshots")),
    )
    op.create_index(
        "ix_connector_benchmark_snapshots_source_created",
        "connector_benchmark_snapshots",
        ["source", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_connector_benchmark_snapshots_source_created", table_name="connector_benchmark_snapshots")
    op.drop_table("connector_benchmark_snapshots")
    op.drop_index("ix_acquisition_daily_reports_date", table_name="acquisition_daily_reports")
    op.drop_table("acquisition_daily_reports")
    op.drop_index("ix_connector_alerts_open_severity", table_name="connector_alerts")
    op.drop_index("ix_connector_alerts_source_created", table_name="connector_alerts")
    op.drop_table("connector_alerts")
    op.drop_index("ix_collector_runs_success_created", table_name="collector_runs")
    op.drop_index("ix_collector_runs_source_created", table_name="collector_runs")
    op.drop_table("collector_runs")
