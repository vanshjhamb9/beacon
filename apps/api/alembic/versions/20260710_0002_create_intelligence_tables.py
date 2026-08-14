"""Create intelligence layer tables.

Revision ID: 20260710_0002
Revises: 20260710_0001
Create Date: 2026-07-10 15:38:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260710_0002"
down_revision: str | None = "20260710_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _base_columns() -> list[sa.Column[object]]:
    return [
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade() -> None:
    op.create_table(
        "companies",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("primary_domain", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("industry", sa.String(length=128), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("signal_frequency", sa.Integer(), nullable=False),
        sa.Column("memory_summary", sa.Text(), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_companies")),
        sa.UniqueConstraint("normalized_name", name="uq_companies_normalized_name"),
    )
    op.create_index("ix_companies_last_seen_at", "companies", ["last_seen_at"])
    op.create_index("ix_companies_primary_domain", "companies", ["primary_domain"])
    op.create_index("ix_companies_signal_frequency", "companies", ["signal_frequency"])

    op.create_table(
        "people",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("normalized_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("attributes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_people_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_people")),
        sa.UniqueConstraint("normalized_name", "company_id", name="uq_people_name_company"),
    )
    op.create_index("ix_people_company_id", "people", ["company_id"])
    op.create_index("ix_people_normalized_name", "people", ["normalized_name"])

    op.create_table(
        "domains",
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_domains_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_domains")),
        sa.UniqueConstraint("domain", name="uq_domains_domain"),
    )
    op.create_index("ix_domains_company_id", "domains", ["company_id"])

    op.create_table(
        "company_aliases",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("normalized_alias", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_aliases_company_id_companies")),
        sa.ForeignKeyConstraint(["evidence_event_id"], ["raw_events.id"], name=op.f("fk_company_aliases_evidence_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_aliases")),
        sa.UniqueConstraint("company_id", "normalized_alias", name="uq_company_aliases_company_alias"),
    )
    op.create_index("ix_company_aliases_normalized_alias", "company_aliases", ["normalized_alias"])

    op.create_table(
        "classified_signals",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("subcategory", sa.String(length=128), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("business_function", sa.String(length=128), nullable=False),
        sa.Column("urgency", sa.String(length=32), nullable=False),
        sa.Column("positive_or_negative", sa.String(length=32), nullable=False),
        sa.Column("source_confidence", sa.Float(), nullable=False),
        sa.Column("entity_confidence", sa.Float(), nullable=False),
        sa.Column("classification_confidence", sa.Float(), nullable=False),
        sa.Column("freshness_score", sa.Float(), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("overall_confidence", sa.Float(), nullable=False),
        sa.Column("confidence_explanation", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_classified_signals_company_id_companies")),
        sa.ForeignKeyConstraint(["event_id"], ["raw_events.id"], name=op.f("fk_classified_signals_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_classified_signals")),
        sa.UniqueConstraint("event_id", "company_id", "category", name="uq_classified_signals_event_company_category"),
    )
    op.create_index("ix_classified_signals_category", "classified_signals", ["category"])
    op.create_index("ix_classified_signals_company_created", "classified_signals", ["company_id", "created_at"])
    op.create_index("ix_classified_signals_overall_confidence", "classified_signals", ["overall_confidence"])
    op.create_index("ix_classified_signals_urgency", "classified_signals", ["urgency"])

    op.create_table(
        "signal_entities",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("person_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("domain_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("value", sa.String(length=512), nullable=False),
        sa.Column("normalized_value", sa.String(length=512), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_signal_entities_company_id_companies")),
        sa.ForeignKeyConstraint(["domain_id"], ["domains.id"], name=op.f("fk_signal_entities_domain_id_domains")),
        sa.ForeignKeyConstraint(["event_id"], ["raw_events.id"], name=op.f("fk_signal_entities_event_id_raw_events")),
        sa.ForeignKeyConstraint(["person_id"], ["people.id"], name=op.f("fk_signal_entities_person_id_people")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_signal_entities")),
    )
    op.create_index("ix_signal_entities_company_id", "signal_entities", ["company_id"])
    op.create_index("ix_signal_entities_entity_type_value", "signal_entities", ["entity_type", "normalized_value"])
    op.create_index("ix_signal_entities_event_id", "signal_entities", ["event_id"])

    op.create_table(
        "company_timelines",
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], name=op.f("fk_company_timelines_company_id_companies")),
        sa.ForeignKeyConstraint(["event_id"], ["raw_events.id"], name=op.f("fk_company_timelines_event_id_raw_events")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_timelines")),
        sa.UniqueConstraint("company_id", "event_id", "signal_type", name="uq_company_timeline_item"),
    )
    op.create_index("ix_company_timelines_company_timestamp", "company_timelines", ["company_id", "timestamp"])
    op.create_index("ix_company_timelines_signal_type", "company_timelines", ["signal_type"])

    op.create_table(
        "company_relationships",
        sa.Column("source_company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_company_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relationship_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["evidence_event_id"], ["raw_events.id"], name=op.f("fk_company_relationships_evidence_event_id_raw_events")),
        sa.ForeignKeyConstraint(["source_company_id"], ["companies.id"], name=op.f("fk_company_relationships_source_company_id_companies")),
        sa.ForeignKeyConstraint(["target_company_id"], ["companies.id"], name=op.f("fk_company_relationships_target_company_id_companies")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_company_relationships")),
    )
    op.create_index("ix_company_relationships_source_company", "company_relationships", ["source_company_id"])
    op.create_index("ix_company_relationships_target_company", "company_relationships", ["target_company_id"])
    op.create_index("ix_company_relationships_type", "company_relationships", ["relationship_type"])

    op.create_table(
        "knowledge_graph_nodes",
        sa.Column("node_type", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=128), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_graph_nodes")),
        sa.UniqueConstraint("node_type", "external_id", name="uq_knowledge_graph_nodes_type_external"),
    )
    op.create_index("ix_knowledge_graph_nodes_label", "knowledge_graph_nodes", ["label"])
    op.create_index("ix_knowledge_graph_nodes_type", "knowledge_graph_nodes", ["node_type"])

    op.create_table(
        "knowledge_graph_edges",
        sa.Column("from_node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_node_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("edge_type", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_event_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("properties", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        *_base_columns(),
        sa.ForeignKeyConstraint(["evidence_event_id"], ["raw_events.id"], name=op.f("fk_knowledge_graph_edges_evidence_event_id_raw_events")),
        sa.ForeignKeyConstraint(["from_node_id"], ["knowledge_graph_nodes.id"], name=op.f("fk_knowledge_graph_edges_from_node_id_knowledge_graph_nodes")),
        sa.ForeignKeyConstraint(["to_node_id"], ["knowledge_graph_nodes.id"], name=op.f("fk_knowledge_graph_edges_to_node_id_knowledge_graph_nodes")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_graph_edges")),
        sa.UniqueConstraint("from_node_id", "to_node_id", "edge_type", name="uq_knowledge_graph_edges_triplet"),
    )
    op.create_index("ix_knowledge_graph_edges_from", "knowledge_graph_edges", ["from_node_id"])
    op.create_index("ix_knowledge_graph_edges_to", "knowledge_graph_edges", ["to_node_id"])
    op.create_index("ix_knowledge_graph_edges_type", "knowledge_graph_edges", ["edge_type"])


def downgrade() -> None:
    op.drop_table("knowledge_graph_edges")
    op.drop_table("knowledge_graph_nodes")
    op.drop_table("company_relationships")
    op.drop_table("company_timelines")
    op.drop_table("signal_entities")
    op.drop_table("classified_signals")
    op.drop_table("company_aliases")
    op.drop_table("domains")
    op.drop_table("people")
    op.drop_table("companies")
