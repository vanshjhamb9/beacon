"""Tests for connector configuration loading."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from opportunity_connector_platform.connector_config import ConnectorConfig, ConnectorConfigLoader


class TestConnectorConfig:
    def test_default(self):
        cfg = ConnectorConfig(connector_id="test")
        assert cfg.connector_id == "test"
        assert cfg.enabled is False
        assert cfg.interval == 300
        assert cfg.priority == "normal"
        assert cfg.rate_limit == "unknown"
        assert cfg.authentication == "none"
        assert cfg.timeout == 30
        assert cfg.max_concurrency == 1
        assert cfg.dependencies == ()
        assert cfg.retry_attempts == 3
        assert cfg.retry_backoff_seconds == 60
        assert cfg.metadata == {}

    def test_custom(self):
        cfg = ConnectorConfig(
            connector_id="github",
            enabled=True,
            interval=60,
            priority="high",
            rate_limit="5000/hour",
            authentication="token",
            timeout=60,
            max_concurrency=2,
            dependencies=("auth",),
            retry_attempts=5,
            retry_backoff_seconds=120,
            metadata={"env": "prod"},
        )
        assert cfg.enabled is True
        assert cfg.interval == 60
        assert cfg.priority == "high"
        assert cfg.rate_limit == "5000/hour"
        assert cfg.authentication == "token"
        assert cfg.timeout == 60
        assert cfg.max_concurrency == 2
        assert cfg.dependencies == ("auth",)
        assert cfg.retry_attempts == 5
        assert cfg.retry_backoff_seconds == 120
        assert cfg.metadata == {"env": "prod"}

    def test_frozen(self):
        cfg = ConnectorConfig(connector_id="test")
        with pytest.raises(AttributeError):
            cfg.enabled = True  # type: ignore[misc]


class TestConnectorConfigLoader:
    def test_load_missing_file(self, tmp_path: Path):
        loader = ConnectorConfigLoader()
        result = loader.load(tmp_path / "nonexistent.yaml")
        assert result == {}

    def test_load_empty_file(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text("")
        loader = ConnectorConfigLoader()
        result = loader.load(path)
        assert result == {}

    def test_load_comments_only(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text("# comment\n# another comment\n")
        loader = ConnectorConfigLoader()
        result = loader.load(path)
        assert result == {}

    def test_load_single_connector(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text(dedent("""\
            github:
              enabled: true
              interval: 300
              priority: high
              rate_limit: "5000/hour"
              authentication: token
        """))
        loader = ConnectorConfigLoader()
        result = loader.load(path)
        assert "github" in result
        assert result["github"].enabled is True
        assert result["github"].interval == 300
        assert result["github"].priority == "high"
        assert result["github"].rate_limit == "5000/hour"
        assert result["github"].authentication == "token"

    def test_load_multiple_connectors(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text(dedent("""\
            github:
              enabled: true
              interval: 300
            google_news:
              enabled: false
              interval: 900
        """))
        loader = ConnectorConfigLoader()
        result = loader.load(path)
        assert len(result) == 2
        assert result["github"].enabled is True
        assert result["google_news"].enabled is False

    def test_load_defaults_missing_fields(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text(dedent("""\
            rss:
              enabled: true
        """))
        loader = ConnectorConfigLoader()
        result = loader.load(path)
        assert result["rss"].interval == 300
        assert result["rss"].priority == "normal"
        assert result["rss"].authentication == "none"

    def test_load_disabled_connector(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text(dedent("""\
            linkedin:
              enabled: false
              interval: 1800
              priority: high
        """))
        loader = ConnectorConfigLoader()
        result = loader.load(path)
        assert result["linkedin"].enabled is False

    def test_default_method(self):
        loader = ConnectorConfigLoader()
        cfg = loader.default("test_connector")
        assert cfg.connector_id == "test_connector"
        assert cfg.enabled is False

    def test_load_with_dependencies(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text(dedent("""\
            enrich:
              enabled: true
              dependencies: "auth,lookup"
        """))
        loader = ConnectorConfigLoader()
        result = loader.load(path)
        assert result["enrich"].dependencies == ("auth", "lookup")

    def test_load_with_retry_config(self, tmp_path: Path):
        path = tmp_path / "config.yaml"
        path.write_text(dedent("""\
            retry_test:
              enabled: true
              retry_attempts: 5
              retry_backoff_seconds: 120
        """))
        loader = ConnectorConfigLoader()
        result = loader.load(path)
        assert result["retry_test"].retry_attempts == 5
        assert result["retry_test"].retry_backoff_seconds == 120

    def test_load_real_config(self):
        loader = ConnectorConfigLoader()
        config_path = Path(__file__).parent.parent.parent / "packages" / "opportunity_connector_platform" / "connector.yaml"
        if config_path.exists():
            result = loader.load(config_path)
            assert len(result) >= 2
            assert "github" in result
