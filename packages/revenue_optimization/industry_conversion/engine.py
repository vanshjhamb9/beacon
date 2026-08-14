from __future__ import annotations

from collections import defaultdict

from revenue_optimization.models.types import (
    CaseStudyRecommendation,
    FounderMetrics,
    IndustryMetrics,
    OfferMetrics,
    OutreachEvent,
)


def _rate(num: int, den: int) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


class IndustryConversionEngine:
    def analyze(self, events: list[OutreachEvent]) -> list[IndustryMetrics]:
        buckets: dict[str, list[OutreachEvent]] = defaultdict(list)
        for e in events:
            if e.industry:
                buckets[e.industry].append(e)
        rows: list[tuple[float, IndustryMetrics]] = []
        for industry, items in buckets.items():
            n = len(items)
            delivered = sum(1 for e in items if e.delivered) or n
            opened = sum(1 for e in items if e.opened)
            replied = sum(1 for e in items if e.replied)
            meetings = sum(1 for e in items if e.meeting_booked)
            proposals = sum(1 for e in items if e.proposal_sent)
            wins = sum(1 for e in items if e.closed_won)
            revenue = sum(e.deal_value for e in items if e.closed_won)
            deal_sizes = [e.deal_value for e in items if e.closed_won and e.deal_value > 0]
            cycles = [max(1.0, (e.reply_hours or 24) / 24.0) for e in items if e.closed_won]
            composite = (
                _rate(opened, delivered)
                + _rate(replied, delivered) * 1.5
                + _rate(meetings, delivered) * 2
                + _rate(wins, delivered) * 3
                + min(50.0, revenue * 0.01)
            )
            rows.append(
                (
                    composite,
                    IndustryMetrics(
                        industry=industry,
                        open_rate=_rate(opened, delivered),
                        reply_rate=_rate(replied, delivered),
                        meeting_rate=_rate(meetings, delivered),
                        proposal_rate=_rate(proposals, delivered),
                        close_rate=_rate(wins, delivered),
                        average_deal_size=round(sum(deal_sizes) / len(deal_sizes), 2) if deal_sizes else 0.0,
                        sales_cycle_days=round(sum(cycles) / len(cycles), 2) if cycles else 0.0,
                        revenue=round(revenue, 2),
                        rank=0,
                        confidence=min(95.0, 35.0 + n * 4.0),
                        evidence=[f"events:{n}", f"wins:{wins}"],
                    ),
                )
            )
        rows.sort(key=lambda x: (-x[0], x[1].industry))
        return [m.model_copy(update={"rank": i, "evidence": m.evidence + [f"rank:{i}"]}) for i, (_, m) in enumerate(rows, start=1)]


class FounderPerformanceEngine:
    def analyze(self, events: list[OutreachEvent]) -> FounderMetrics:
        founder = [e for e in events if e.founder_actor]
        companies = len({e.company_name for e in founder if e.company_name})
        emails = sum(1 for e in founder if e.channel == "email")
        wa = sum(1 for e in founder if e.channel == "whatsapp")
        booked = sum(1 for e in founder if e.meeting_booked)
        completed = sum(1 for e in founder if e.meeting_completed)
        proposals = sum(1 for e in founder if e.proposal_sent)
        closed = sum(1 for e in founder if e.closed_won)
        revenue = sum(e.deal_value for e in founder if e.closed_won)
        delays = [e.delay_days * 24 for e in founder if e.delay_days is not None]
        replies = [e.reply_hours for e in founder if e.reply_hours is not None]
        pipeline = min(100.0, booked * 8.0 + proposals * 10.0 + closed * 15.0 + emails * 0.5)
        # weekly trend proxy: reply+meeting density
        trend = min(100.0, _rate(sum(1 for e in founder if e.replied or e.meeting_booked), max(1, len(founder))) - 20.0)
        return FounderMetrics(
            companies_contacted=companies,
            emails_sent=emails,
            whatsapp_messages=wa,
            meetings_booked=booked,
            meetings_completed=completed,
            proposals_sent=proposals,
            deals_closed=closed,
            revenue=round(revenue, 2),
            followup_speed_hours=round(sum(delays) / len(delays), 2) if delays else 0.0,
            average_response_time_hours=round(sum(replies) / len(replies), 2) if replies else 0.0,
            pipeline_health=round(pipeline, 2),
            weekly_trend=round(trend, 2),
            confidence=min(95.0, 30.0 + len(founder) * 2.0),
            evidence=[f"founder_events:{len(founder)}", f"revenue:{revenue}"],
        )


class OfferIntelligenceEngine:
    def analyze(self, events: list[OutreachEvent]) -> list[OfferMetrics]:
        buckets: dict[str, list[OutreachEvent]] = defaultdict(list)
        for e in events:
            if e.offer:
                buckets[e.offer].append(e)
        out: list[OfferMetrics] = []
        for offer, items in buckets.items():
            interest = sum(1 for e in items if e.opened or e.replied or e.calendly_clicks)
            meetings = sum(1 for e in items if e.meeting_booked)
            wins = sum(1 for e in items if e.closed_won)
            revenue = sum(e.deal_value for e in items if e.closed_won)
            score = interest * 1.0 + meetings * 5.0 + wins * 12.0 + revenue * 0.01
            out.append(
                OfferMetrics(
                    offer=offer,
                    interest=interest,
                    meetings=meetings,
                    wins=wins,
                    revenue=round(revenue, 2),
                    score=round(score, 2),
                    confidence=min(95.0, 35.0 + len(items) * 4.0),
                    evidence=[f"offer:{offer}", f"wins:{wins}"],
                )
            )
        out.sort(key=lambda x: (-x.score, x.offer))
        return out


class CaseStudyIntelligenceEngine:
    def recommend(self, events: list[OutreachEvent], assets: list[dict]) -> list[CaseStudyRecommendation]:
        if not events and not assets:
            return []
        industries = Counterish(e.industry for e in events if e.industry)
        sizes = Counterish(e.company_size_band for e in events if e.company_size_band)
        pains = Counterish(p for e in events for p in e.pain_points)
        techs = Counterish(t for e in events for t in e.technology)
        personas = Counterish(e.buyer_persona for e in events if e.buyer_persona)
        out: list[CaseStudyRecommendation] = []
        for asset in assets:
            score = 40.0
            reasons = []
            ind = asset.get("industry")
            if ind and ind in industries:
                score += 20.0
                reasons.append(f"industry:{ind}")
            size = asset.get("company_size")
            if size and size in sizes:
                score += 10.0
                reasons.append(f"size:{size}")
            for p in asset.get("pain_points") or []:
                if p in pains:
                    score += 8.0
                    reasons.append(f"pain:{p}")
            for t in asset.get("technology") or []:
                if t in techs:
                    score += 6.0
                    reasons.append(f"tech:{t}")
            persona = asset.get("buyer_persona")
            if persona and persona in personas:
                score += 10.0
                reasons.append(f"persona:{persona}")
            out.append(
                CaseStudyRecommendation(
                    asset_type=str(asset.get("asset_type") or "case_study"),
                    asset_id=str(asset.get("asset_id") or asset.get("title") or "asset"),
                    title=str(asset.get("title") or "Case Study"),
                    reason=", ".join(reasons) or "general_fit",
                    industry=ind,
                    company_size=size,
                    score=round(min(95.0, score), 2),
                    confidence=min(90.0, 40.0 + len(reasons) * 10.0),
                    evidence=reasons or ["default:portfolio"],
                )
            )
        out.sort(key=lambda x: (-x.score, x.title))
        return out[:10]


def Counterish(values) -> dict[str, int]:
    from collections import Counter

    return dict(Counter(values))
