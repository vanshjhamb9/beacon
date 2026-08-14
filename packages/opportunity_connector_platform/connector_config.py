"""Connector configuration loading without runtime dependencies.

One config file: connector.yaml. No hardcoding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ConnectorConfig:
    connector_id: str
    enabled: bool = False
    interval: int = 300
    priority: str = "normal"
    rate_limit: str = "unknown"
    authentication: str = "none"
    timeout: int = 30
    max_concurrency: int = 1
    dependencies: tuple[str, ...] = field(default_factory=tuple)
    retry_attempts: int = 3
    retry_backoff_seconds: int = 60
    metadata: dict[str, str] = field(default_factory=dict)


class ConnectorConfigLoader:
    """Deterministic YAML-like config loader."""

    def load(self, path: Path) -> dict[str, ConnectorConfig]:
        if not path.exists():
            return {}
        configs: dict[str, dict[str, str]] = {}
        current: str | None = None
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.rstrip()
            if not line or line.lstrip().startswith("#"):
                continue
            if not line.startswith(" ") and line.endswith(":"):
                current = line[:-1].strip()
                configs[current] = {}
                continue
            if current and ":" in line:
                key, value = line.strip().split(":", 1)
                configs[current][key.strip()] = value.strip().strip('"')
        return {
            connector_id: ConnectorConfig(
                connector_id=connector_id,
                enabled=values.get("enabled", "false").lower() == "true",
                interval=int(values.get("interval", 300)),
                priority=values.get("priority", "normal"),
                rate_limit=values.get("rate_limit", "unknown"),
                authentication=values.get("authentication", "none"),
                timeout=int(values.get("timeout", 30)),
                max_concurrency=int(values.get("max_concurrency", 1)),
                dependencies=tuple(
                    d.strip() for d in values.get("dependencies", "").split(",") if d.strip()
                ),
                retry_attempts=int(values.get("retry_attempts", 3)),
                retry_backoff_seconds=int(values.get("retry_backoff_seconds", 60)),
                metadata={k[5:]: v for k, v in values.items() if k.startswith("meta_")},
            )
            for connector_id, values in configs.items()
        }

    def default(self, connector_id: str) -> ConnectorConfig:
        return ConnectorConfig(connector_id=connector_id)
