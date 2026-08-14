"""Connector health scoring and normalization."""

from __future__ import annotations

from datetime import datetime

from operations_center.models import KNOWN_CONNECTORS, ConnectorHealthView


def normalize_connector_name(name: str) -> str:
    key = (name or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "github": "github_trending",
        "gh": "github_trending",
        "hn": "hacker_news",
        "producthunt": "product_hunt",
        "ph": "product_hunt",
        "hunter_io": "hunter",
        "pdl": "people_data_labs",
        "people_data_lab": "people_data_labs",
        "gmaps": "google_maps",
        "play_store": "google_play",
        "appstore": "app_store",
    }
    return aliases.get(key, key)


def score_connector(
    *,
    connector: str,
    enabled: bool,
    records_today: int = 0,
    records_total: int = 0,
    success_rate: float = 0.0,
    error_count: int = 0,
    avg_runtime: float = 0.0,
    rate_limited: bool = False,
    last_run: datetime | None = None,
    last_success: datetime | None = None,
    last_failure: datetime | None = None,
    detail: str = "",
) -> ConnectorHealthView:
    name = normalize_connector_name(connector)
    detail_l = (detail or "").lower()
    if not enabled:
        if "reserved" in detail_l or "not configured" in detail_l:
            status = "idle"
            healthy = False
        else:
            status = "disabled"
            healthy = False
    elif rate_limited:
        status = "rate_limited"
        healthy = False
    elif "reserved" in detail_l or "not configured" in detail_l:
        status = "idle"
        healthy = False
    elif "token" in detail_l or "waiting" in detail_l:
        status = "waiting_token"
        healthy = False
    elif "cloudflare" in detail_l:
        status = "blocked"
        healthy = False
    elif success_rate >= 90.0 and error_count == 0:
        status = "healthy"
        healthy = True
    elif success_rate >= 70.0:
        status = "degraded"
        healthy = True
    elif last_success is None and records_total == 0:
        status = "idle"
        healthy = False
    else:
        status = "failing"
        healthy = False

    return ConnectorHealthView(
        connector=name,
        enabled=enabled,
        healthy=healthy,
        status=status,
        last_run=last_run,
        last_success=last_success,
        last_failure=last_failure,
        success_rate=round(success_rate, 1),
        error_count=error_count,
        records_today=records_today,
        records_total=records_total,
        avg_runtime=round(avg_runtime, 2),
        rate_limited=rate_limited,
        detail=detail,
    )


def ensure_known_connectors(rows: list[ConnectorHealthView]) -> list[ConnectorHealthView]:
    """Guarantee every known connector appears so future providers need no redesign."""
    by_name = {r.connector: r for r in rows}
    out: list[ConnectorHealthView] = []
    for name in KNOWN_CONNECTORS:
        if name in by_name:
            out.append(by_name[name])
        else:
            out.append(
                score_connector(
                    connector=name,
                    enabled=False,
                    detail="Not configured — reserved for future integration",
                )
            )
    # Preserve any unexpected connectors discovered at runtime.
    for name, row in by_name.items():
        if name not in KNOWN_CONNECTORS:
            out.append(row)
    return out
