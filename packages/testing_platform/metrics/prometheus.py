from __future__ import annotations

from typing import Any


def render_prometheus(metrics: dict[str, Any]) -> str:
    """Render a flat metrics dict as Prometheus text exposition format."""
    lines: list[str] = []
    for key, value in metrics.items():
        name = str(key).replace(".", "_").replace("-", "_")
        if isinstance(value, dict):
            for label, labeled_value in value.items():
                if isinstance(labeled_value, (int, float)):
                    lines.append(f'{name}{{label="{label}"}} {labeled_value}')
            continue
        if isinstance(value, bool):
            lines.append(f"{name} {1 if value else 0}")
        elif isinstance(value, (int, float)):
            lines.append(f"{name} {value}")
    return "\n".join(lines) + ("\n" if lines else "")
