"""Migration tests for validation engine."""

from __future__ import annotations


class TestValidationEngineMigration:
    def test_migration_file_exists(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        assert os.path.exists(migration_path)

    def test_migration_has_upgrade_function(self) -> None:
        import importlib.util
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        spec = importlib.util.spec_from_file_location("migration", migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "upgrade")
        assert callable(module.upgrade)

    def test_migration_has_downgrade_function(self) -> None:
        import importlib.util
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        spec = importlib.util.spec_from_file_location("migration", migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, "downgrade")
        assert callable(module.downgrade)

    def test_migration_creates_validation_events_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "validation_events" in content

    def test_migration_creates_lead_outcomes_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "lead_outcomes" in content

    def test_migration_creates_reply_events_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "reply_events" in content

    def test_migration_creates_meeting_events_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "meeting_events" in content

    def test_migration_creates_proposal_events_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "proposal_events" in content

    def test_migration_creates_deal_events_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "deal_events" in content

    def test_migration_creates_validation_timelines_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "validation_timelines" in content

    def test_migration_creates_connector_roi_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "connector_roi" in content

    def test_migration_creates_service_roi_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "service_roi" in content

    def test_migration_creates_industry_roi_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "industry_roi" in content

    def test_migration_creates_persona_roi_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "persona_roi" in content

    def test_migration_creates_trigger_roi_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "trigger_roi" in content

    def test_migration_creates_objection_events_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "objection_events" in content

    def test_migration_creates_validation_snapshots_table(self) -> None:
        import os
        migration_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "apps", "api", "alembic", "versions",
            "20260729_0053_validation_engine.py",
        )
        with open(migration_path) as f:
            content = f.read()
        assert "validation_snapshots" in content
