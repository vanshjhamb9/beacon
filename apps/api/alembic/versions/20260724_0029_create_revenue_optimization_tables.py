"""Create revenue optimization (ROIP) tables.

Revision ID: 20260724_0029
Revises: 20260724_0028
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260724_0029"
down_revision: str | None = "20260724_0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base():
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def _json():
    return postgresql.JSONB(astext_type=sa.Text())


TABLES = [
    ("roip_email_metrics", [sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False), sa.Column("confidence", sa.Float(), nullable=False, server_default="0")], ["ix_roip_email_created"]),
    ("roip_subject_performance", [sa.Column("subject", sa.String(512), nullable=False), sa.Column("rank", sa.Integer(), nullable=False, server_default="0"), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_subject_created"]),
    ("roip_cta_performance", [sa.Column("cta", sa.String(128), nullable=False), sa.Column("score", sa.Float(), nullable=False, server_default="0"), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_cta_created"]),
    ("roip_followup_patterns", [sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False), sa.Column("confidence", sa.Float(), nullable=False, server_default="0")], ["ix_roip_followup_created"]),
    ("roip_industry_metrics", [sa.Column("industry", sa.String(128), nullable=False), sa.Column("rank", sa.Integer(), nullable=False, server_default="0"), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_industry_created"]),
    ("roip_founder_metrics", [sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False), sa.Column("revenue", sa.Float(), nullable=False, server_default="0")], ["ix_roip_founder_created"]),
    ("roip_offer_metrics", [sa.Column("offer", sa.String(128), nullable=False), sa.Column("score", sa.Float(), nullable=False, server_default="0"), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_offer_created"]),
    ("roip_case_study_metrics", [sa.Column("asset_id", sa.String(128), nullable=False), sa.Column("score", sa.Float(), nullable=False, server_default="0"), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_case_created"]),
    ("roip_reply_analysis", [sa.Column("reply_id", sa.String(128), nullable=False), sa.Column("category", sa.String(64), nullable=False), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_reply_created"]),
    ("roip_learning_events", [sa.Column("insight_type", sa.String(64), nullable=False), sa.Column("modifies_production", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_learning_created"]),
    ("roip_revenue_benchmarks", [sa.Column("period", sa.String(32), nullable=False), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_bench_created"]),
    ("roip_recommendations", [sa.Column("recommendation_id", sa.String(64), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("requires_founder_approval", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("modifies_production", sa.Boolean(), nullable=False, server_default=sa.text("false")), sa.Column("payload", _json(), nullable=False), sa.Column("evidence", _json(), nullable=False)], ["ix_roip_recs_created"]),
]


def upgrade() -> None:
    for name, cols, indexes in TABLES:
        op.create_table(
            name,
            *_base(),
            *cols,
            sa.Column("scoring_version", sa.String(64), nullable=False, server_default="roip-v1"),
            sa.PrimaryKeyConstraint("id", name=op.f(f"pk_{name}")),
        )
        for idx in indexes:
            op.create_index(idx, name, ["created_at"])


def downgrade() -> None:
    for name, _cols, indexes in reversed(TABLES):
        for idx in indexes:
            op.drop_index(idx, table_name=name)
        op.drop_table(name)
