from __future__ import annotations

from typing import Any

from revenue_readiness_validation.models.types import OpportunityAuditRow


class OpportunityExplainabilityEngine:
    """Hide opportunities that cannot answer why/why-now/evidence/source."""

    REQUIRED = (
        "why_collected",
        "why_interesting",
        "why_now",
        "evidence",
        "source",
        "collected_at",
    )

    def audit(self, payload: dict[str, Any]) -> OpportunityAuditRow:
        missing: list[str] = []
        why_collected = payload.get("why_collected") or payload.get("source") or payload.get("collector")
        why_interesting = payload.get("why_interesting") or payload.get("narrative") or payload.get("summary")
        why_now = payload.get("why_now") or payload.get("intent") or payload.get("timing")
        evidence = payload.get("evidence") or []
        source = payload.get("source") or payload.get("collector")
        collected_at = payload.get("collected_at") or payload.get("created_at")
        rules = list(payload.get("rules_matched") or payload.get("score_breakdown_keys") or [])

        if not why_collected:
            missing.append("why_collected")
        if not why_interesting or (isinstance(why_interesting, str) and len(why_interesting.strip()) < 12):
            missing.append("why_interesting")
        if not why_now:
            missing.append("why_now")
        if not evidence:
            missing.append("evidence")
        if not source:
            missing.append("source")
        if not collected_at:
            missing.append("collected_at")

        explainable = len(missing) == 0
        return OpportunityAuditRow(
            opportunity_id=str(payload.get("opportunity_id") or payload.get("id") or ""),
            company_id=str(payload.get("company_id") or ""),
            company_name=str(payload.get("company_name") or "UNKNOWN"),
            explainable=explainable,
            hide=not explainable,
            why_collected=str(why_collected) if why_collected else None,
            why_interesting=str(why_interesting) if why_interesting else None,
            why_now=str(why_now) if why_now else None,
            evidence_count=len(evidence) if hasattr(evidence, "__len__") else 0,
            source=str(source) if source else None,
            collector=str(payload.get("collector") or source or "") or None,
            collected_at=collected_at,
            rules_matched=[str(r) for r in rules[:12]],
            missing=missing,
        )
