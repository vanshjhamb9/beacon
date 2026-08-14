"""Add Opportunity Intelligence Platform columns append-only.

Sprint 36A requested revision 20260727_0049, but that revision already exists
for Lead Intelligence Explorer in this repository. This linear follow-up keeps
the migration chain valid and adds only nullable columns/indexes to the existing
opportunity tables created by 20260710_0005.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260728_0050"
down_revision = "20260727_0049"
branch_labels = None
depends_on = None


def _columns(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {column["name"] for column in inspector.get_columns(table_name)}


def _add_missing(table_name: str, column: sa.Column[object]) -> None:
    if column.name not in _columns(table_name):
        op.add_column(table_name, column)


def _indexes(table_name: str) -> set[str]:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return {index["name"] for index in inspector.get_indexes(table_name)}


def _create_index_missing(name: str, table_name: str, columns: list[str]) -> None:
    if name not in _indexes(table_name):
        op.create_index(name, table_name, columns)


def upgrade() -> None:
    opportunity_columns = [
        sa.Column("website", sa.String(1024), nullable=True),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("country", sa.String(128), nullable=True),
        sa.Column("signal_type", sa.String(128), nullable=True),
        sa.Column("signal_source", sa.String(128), nullable=True),
        sa.Column("signal_category", sa.String(64), nullable=True),
        sa.Column("signal_title", sa.String(255), nullable=True),
        sa.Column("signal_summary", sa.Text(), nullable=True),
        sa.Column("signal_url", sa.String(2048), nullable=True),
        sa.Column("signal_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signal_age_days", sa.Integer(), nullable=True),
        sa.Column("buying_window", sa.String(32), nullable=True),
        sa.Column("intent_score", sa.Float(), nullable=True),
        sa.Column("pain_score", sa.Float(), nullable=True),
        sa.Column("budget_score", sa.Float(), nullable=True),
        sa.Column("growth_score", sa.Float(), nullable=True),
        sa.Column("freshness_score", sa.Float(), nullable=True),
        sa.Column("evidence_score", sa.Float(), nullable=True),
        sa.Column("icp_score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("trust", sa.Float(), nullable=True),
        sa.Column("dedupe_key", sa.String(191), nullable=True),
    ]
    for column in opportunity_columns:
        _add_missing("opportunities", column)

    evidence_columns = [
        sa.Column("provider", sa.String(128), nullable=True),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trust", sa.Float(), nullable=True),
    ]
    for column in evidence_columns:
        _add_missing("opportunity_evidence", column)

    score_columns = [
        sa.Column("intent", sa.Float(), nullable=True),
        sa.Column("budget", sa.Float(), nullable=True),
        sa.Column("growth", sa.Float(), nullable=True),
        sa.Column("timing", sa.Float(), nullable=True),
        sa.Column("pain", sa.Float(), nullable=True),
        sa.Column("freshness", sa.Float(), nullable=True),
        sa.Column("evidence", sa.Float(), nullable=True),
        sa.Column("icp", sa.Float(), nullable=True),
        sa.Column("final_score", sa.Float(), nullable=True),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=True),
    ]
    for column in score_columns:
        _add_missing("opportunity_scores", column)

    _create_index_missing("ix_opportunities_signal_category", "opportunities", ["signal_category"])
    _create_index_missing("ix_opportunities_buying_window", "opportunities", ["buying_window"])
    _create_index_missing("ix_opportunities_dedupe_key", "opportunities", ["dedupe_key"])
    _create_index_missing("ix_opportunity_scores_calculated", "opportunity_scores", ["calculated_at"])
    _create_index_missing("ix_opportunity_evidence_provider", "opportunity_evidence", ["provider"])


def downgrade() -> None:
    for index_name, table_name in [
        ("ix_opportunity_evidence_provider", "opportunity_evidence"),
        ("ix_opportunity_scores_calculated", "opportunity_scores"),
        ("ix_opportunities_dedupe_key", "opportunities"),
        ("ix_opportunities_buying_window", "opportunities"),
        ("ix_opportunities_signal_category", "opportunities"),
    ]:
        if index_name in _indexes(table_name):
            op.drop_index(index_name, table_name=table_name)

    for table_name, columns in [
        (
            "opportunity_scores",
            [
                "calculated_at",
                "final_score",
                "icp",
                "evidence",
                "freshness",
                "pain",
                "timing",
                "growth",
                "budget",
                "intent",
            ],
        ),
        (
            "opportunity_evidence",
            ["trust", "captured_at", "description", "title", "url", "provider"],
        ),
        (
            "opportunities",
            [
                "dedupe_key",
                "trust",
                "confidence",
                "icp_score",
                "evidence_score",
                "freshness_score",
                "growth_score",
                "budget_score",
                "pain_score",
                "intent_score",
                "buying_window",
                "signal_age_days",
                "signal_timestamp",
                "signal_url",
                "signal_summary",
                "signal_title",
                "signal_category",
                "signal_source",
                "signal_type",
                "country",
                "industry",
                "website",
            ],
        ),
    ]:
        existing = _columns(table_name)
        for column in columns:
            if column in existing:
                op.drop_column(table_name, column)
