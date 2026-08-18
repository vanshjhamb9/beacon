"""Map Lane C opportunities into Lead Engine job rows. Never sends outreach."""

from __future__ import annotations

from typing import Any

from packages.cybersecurity_discovery.pipeline import PipelineResult
from packages.cybersecurity_discovery.workspace_sync import opportunity_to_workspace_lead


def opportunities_to_lead_engine_rows(result: PipelineResult) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for opp in result.sales_ready:
        rows.append(opportunity_to_workspace_lead(opp, outreach=True))
    for opp in result.needs_research:
        rows.append(opportunity_to_workspace_lead(opp, outreach=False))
    return rows
