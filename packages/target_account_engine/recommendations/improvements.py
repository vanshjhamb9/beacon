from __future__ import annotations

from target_account_engine.models.types import ImprovementRecommendation, TargetAccountDecision


class ImprovementAdvisor:
    """Recommend scoring improvements from outcomes. Never auto-retrains."""

    def from_outcome(
        self,
        decision: TargetAccountDecision,
        *,
        outcome: str,
        notes: str | None = None,
    ) -> list[ImprovementRecommendation]:
        outcome_l = outcome.strip().lower()
        recs: list[ImprovementRecommendation] = []
        if outcome_l in {"meeting", "meeting_scheduled", "meeting_booked", "replied"}:
            recs.append(
                ImprovementRecommendation(
                    area="confidence",
                    recommendation="Increase confidence weight for matched ICP buying signals on similar accounts.",
                    reason=f"Positive outcome '{outcome}' on {decision.matched_icp_key or 'unmatched'} tier {decision.tier.value}.",
                    expected_impact=8.0,
                )
            )
        if outcome_l in {"won", "proposal_won", "closed_won"}:
            recs.append(
                ImprovementRecommendation(
                    area="feature_importance",
                    recommendation="Increase fit/intent feature importance for winning ICP attributes.",
                    reason=f"Won deal with revenue score {decision.revenue_opportunity_score}.",
                    expected_impact=12.0,
                )
            )
            for component in decision.score_breakdown:
                if component.value >= 70:
                    recs.append(
                        ImprovementRecommendation(
                            area=component.name,
                            recommendation=f"Preserve or raise weight for strong {component.name} signals.",
                            reason=component.explanation,
                            expected_impact=5.0,
                        )
                    )
        if outcome_l in {"lost", "proposal_lost", "closed_lost"}:
            weak = sorted(decision.score_breakdown, key=lambda c: c.value)[:2]
            for component in weak:
                recs.append(
                    ImprovementRecommendation(
                        area=component.name,
                        recommendation=f"Investigate false positives in {component.name}; consider threshold tuning.",
                        reason=f"Lost deal with weak {component.name}={component.value}. {notes or ''}".strip(),
                        expected_impact=7.0,
                    )
                )
            if decision.accessibility.score < 50:
                recs.append(
                    ImprovementRecommendation(
                        area="accessibility",
                        recommendation="Require verified decision-maker email before auto-pipeline for this ICP.",
                        reason="Lost deal had low accessibility — reachability likely blocked conversion.",
                        expected_impact=9.0,
                    )
                )
        return recs
