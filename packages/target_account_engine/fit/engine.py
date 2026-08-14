from __future__ import annotations

from target_account_engine.matching.icp_matcher import ICPMatcher
from target_account_engine.models.types import EngineScore, ICPProfile, TargetAccountInput


class FitEngine:
    def __init__(self, matcher: ICPMatcher | None = None) -> None:
        self.matcher = matcher or ICPMatcher()

    def score(
        self, item: TargetAccountInput, profiles: list[ICPProfile]
    ) -> tuple[EngineScore, ICPProfile | None]:
        profile, icp_score, evidence = self.matcher.match(item, profiles)
        industry_boost = 10.0 if item.industry else 0.0
        tech_boost = min(15.0, 3.0 * len(item.technologies[:5]))
        growth_boost = min(10.0, 2.5 * len(item.growth_signals[:4]))
        employee_boost = 8.0 if item.employee_count else 0.0
        value = min(
            100.0,
            icp_score * 0.70 + industry_boost + tech_boost + growth_boost + employee_boost,
        )
        explanation = (
            f"Company fit {value:.1f}/100 against ICP '{profile.name if profile else 'none'}' "
            f"(ICP match {icp_score:.1f})."
        )
        return (
            EngineScore(
                score=round(value, 2),
                explanation=explanation,
                evidence=evidence,
                details={"icp_match_score": icp_score, "icp_key": profile.key if profile else None},
            ),
            profile,
        )
