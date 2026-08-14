from __future__ import annotations

from target_account_engine.models.types import EngineScore, TargetAccountInput
from target_account_engine.signals.catalog import INTENT_SIGNAL_WEIGHTS, detect_signals


class IntentEngine:
    def score(self, item: TargetAccountInput) -> EngineScore:
        corpus = (
            item.signals
            + item.hiring_roles
            + item.growth_signals
            + item.pains
            + item.goals
            + item.news
        )
        detected = detect_signals(corpus, INTENT_SIGNAL_WEIGHTS)
        raw = sum(INTENT_SIGNAL_WEIGHTS[name] for name in detected)
        if item.hiring_count >= 5:
            raw += 12.0
            detected.append(f"hiring_volume:{item.hiring_count}")
        if item.funding_days_ago is not None and item.funding_days_ago <= 90:
            raw += 14.0
            detected.append(f"recent_funding:{item.funding_days_ago}d")
        score = min(100.0, raw)
        return EngineScore(
            score=round(score, 2),
            explanation=f"Buying intent {score:.1f}/100 from {len(detected)} active signals.",
            evidence=detected[:12],
            details={"signal_count": len(detected)},
        )
