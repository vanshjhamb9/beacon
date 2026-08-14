from __future__ import annotations

from revenue_operations.models.types import ForecastHorizon, RevenueForecastPack, RevenueOperationsInput


class RevenueForecastEngine:
    """Deterministic multi-horizon forecast from pipeline probabilities."""

    def forecast(self, item: RevenueOperationsInput) -> RevenueForecastPack:
        opps = [o for o in item.opportunities if not o.lost]
        expected = sum(o.pipeline_value * (o.probability / 100.0) for o in opps)
        at_risk = sum(1 for o in item.opportunities if o.at_risk)
        meetings = sum(1 for o in item.opportunities if o.meeting_today or o.meeting_count > 0)
        proposals = sum(1 for o in item.opportunities if o.proposal_pending or o.proposal_count > 0)
        closes = sum(1 for o in item.opportunities if o.won) + max(1, int(round(expected / 40000.0))) if expected else 0
        health = max(0.0, min(100.0, 70.0 + (expected / 10000.0) - (at_risk * 5.0)))
        confidence = max(35.0, min(95.0, 55.0 + (len(opps) * 1.5) - (at_risk * 3.0)))
        week = ForecastHorizon(
            label="this_week",
            amount=round(expected * 0.22, 2),
            confidence=round(min(95.0, confidence + 5), 2),
            expected_meetings=max(meetings, int(round(len(opps) * 0.08))),
            expected_proposals=max(proposals, int(round(len(opps) * 0.05))),
            expected_closes=max(0, int(round(closes * 0.25))),
            evidence=["horizon:week", f"expected_base:{expected}"],
        )
        month = ForecastHorizon(
            label="this_month",
            amount=round(expected * 0.75, 2),
            confidence=round(confidence, 2),
            expected_meetings=max(meetings * 2, int(round(len(opps) * 0.2))),
            expected_proposals=max(proposals * 2, int(round(len(opps) * 0.12))),
            expected_closes=max(0, int(round(closes * 0.6))),
            evidence=["horizon:month"],
        )
        quarter = ForecastHorizon(
            label="quarter",
            amount=round(expected * 2.1, 2),
            confidence=round(max(30.0, confidence - 8), 2),
            expected_meetings=int(round(len(opps) * 0.55)),
            expected_proposals=int(round(len(opps) * 0.35)),
            expected_closes=max(0, int(round(closes * 1.8))),
            evidence=["horizon:quarter"],
        )
        annual = ForecastHorizon(
            label="annual",
            amount=round(expected * 7.5 + float(item.revenue_closed), 2),
            confidence=round(max(25.0, confidence - 15), 2),
            expected_meetings=int(round(len(opps) * 2.0)),
            expected_proposals=int(round(len(opps) * 1.2)),
            expected_closes=max(0, int(round(closes * 6))),
            evidence=["horizon:annual"],
        )
        risks = []
        if at_risk:
            risks.append(f"{at_risk} deals marked at risk")
        if expected < item.revenue_target_week:
            risks.append("Expected revenue below weekly target")
        if not opps:
            risks.append("Empty pipeline")
        return RevenueForecastPack(
            this_week=week,
            this_month=month,
            quarter=quarter,
            annual=annual,
            pipeline_health=round(health, 2),
            risk_analysis=risks,
            confidence_score=round(confidence, 2),
            evidence=[f"opps:{len(opps)}", f"expected:{expected}", f"at_risk:{at_risk}"],
        )
