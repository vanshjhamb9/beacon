from pathlib import Path

from app.models.copilot import (
    SalesDraft,
    SalesFeedback,
    SalesGenerationLog,
    SalesPackage,
    SalesPromptVersion,
    SalesTemplate,
    SalesVersion,
)


def test_copilot_models_tablename_contract() -> None:
    assert SalesPackage.__tablename__ == "sales_packages"
    assert SalesDraft.__tablename__ == "sales_drafts"
    assert SalesTemplate.__tablename__ == "sales_templates"
    assert SalesPromptVersion.__tablename__ == "sales_prompt_versions"
    assert SalesGenerationLog.__tablename__ == "sales_generation_logs"
    assert SalesFeedback.__tablename__ == "sales_feedback"
    assert SalesVersion.__tablename__ == "sales_versions"


def test_migration_0013_defines_required_tables() -> None:
    root = Path(__file__).resolve().parents[2]
    migration = root / "apps" / "api" / "alembic" / "versions" / "20260720_0013_create_sales_copilot_tables.py"
    text = migration.read_text(encoding="utf-8")
    for table in (
        "sales_packages",
        "sales_drafts",
        "sales_templates",
        "sales_prompt_versions",
        "sales_generation_logs",
        "sales_feedback",
        "sales_versions",
    ):
        assert table in text
    assert 'revision: str = "20260720_0013"' in text
    assert 'down_revision: str | None = "20260719_0012"' in text
