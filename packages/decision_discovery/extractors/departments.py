from __future__ import annotations

from collections import Counter
from typing import Any

from decision_discovery.models.types import (
    DecisionMakerCandidate,
    DepartmentEntry,
    DiscoverySourceType,
)


class DepartmentExtractor:
    def extract(
        self,
        makers: list[DecisionMakerCandidate],
        context_intelligence: dict[str, Any],
        lead_profile: dict[str, Any],
    ) -> list[DepartmentEntry]:
        counts: Counter[str] = Counter()
        evidence: dict[str, str] = {}
        sources: dict[str, DiscoverySourceType] = {}

        for maker in makers:
            department = (maker.department or "Leadership").strip()
            counts[department] += 1
            evidence[department] = maker.evidence
            sources[department] = maker.source

        team = lead_profile.get("team_insights") if isinstance(lead_profile.get("team_insights"), dict) else {}
        mapping = {
            "engineering_team_estimate": "Engineering",
            "support_team_estimate": "Support",
            "operations_team_estimate": "Operations",
            "leadership_team_size": "Leadership",
        }
        for key, department in mapping.items():
            value = team.get(key) if isinstance(team, dict) else None
            if isinstance(value, int) and value > 0:
                counts[department] += 1
                evidence[department] = f"Team insight signal: {key}={value}"
                sources[department] = DiscoverySourceType.BEACON_ENRICHMENT

        hiring = str(context_intelligence.get("hiring_pattern") or "")
        if hiring:
            lowered = hiring.lower()
            for department in ("Engineering", "Support", "Operations", "Marketing", "Sales", "Product"):
                if department.lower() in lowered:
                    counts[department] += 1
                    evidence[department] = f"Context hiring pattern mentions {department}"
                    sources[department] = DiscoverySourceType.BEACON_CONTEXT

        departments: list[DepartmentEntry] = []
        for name, count in counts.most_common():
            departments.append(
                DepartmentEntry(
                    name=name,
                    signal_strength=min(100.0, 40.0 + count * 20.0),
                    headcount_signal=evidence.get(name),
                    source=sources.get(name, DiscoverySourceType.BEACON_ENRICHMENT),
                    evidence=evidence.get(name, f"Department inferred from public role evidence ({count} signals)"),
                )
            )
        return departments
