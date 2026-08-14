from __future__ import annotations

from target_account_engine.models.types import EngineScore, TargetAccountInput
from target_account_engine.signals.catalog import URGENCY_SIGNAL_WEIGHTS, detect_signals


class UrgencyEngine:
    def score(self, item: TargetAccountInput) -> EngineScore:
        corpus = item.signals + item.hiring_roles + item.growth_signals + item.pains + item.news + item.goals
        detected = detect_signals(corpus, URGENCY_SIGNAL_WEIGHTS)
        raw = sum(URGENCY_SIGNAL_WEIGHTS[name] for name in detected)
        if item.funding_days_ago is not None and item.funding_days_ago <= 45:
            raw += 18.0
            detected.append(f"funding_within_{item.funding_days_ago}_days")
        if item.hiring_count >= 8:
            raw += 12.0
            detected.append("support_or_ops_hiring_surge")
        website = item.website_metrics or {}
        if website.get("redesign") or website.get("outdated"):
            raw += 10.0
            detected.append("website_redesign_window")
        score = min(100.0, raw)
        return EngineScore(
            score=round(score, 2),
            explanation=f"Urgency {score:.1f}/100 — why-now pressure from {len(detected)} triggers.",
            evidence=detected[:12],
            details={"trigger_count": len(detected)},
        )
