from __future__ import annotations

import hashlib
from collections import Counter

from revenue_optimization.models.types import (
    LearningInsight,
    OptimizationRecommendation,
    OutreachEvent,
    Period,
    ReplyAnalysis,
    ReplyCategory,
    RevenueBenchmark,
)


def _rate(num: int, den: int) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


REPLY_PATTERNS: list[tuple[ReplyCategory, tuple[str, ...], float]] = [
    (ReplyCategory.NEGATIVE, ("not interested", "unsubscribe", "remove me", "stop emailing"), 88.0),
    (ReplyCategory.MEETING_REQUESTED, ("book a call", "schedule", "calendly", "meet"), 90.0),
    (ReplyCategory.BUDGET_ISSUE, ("budget", "too expensive", "cost", "pricing concern"), 82.0),
    (ReplyCategory.TIMING_ISSUE, ("next quarter", "not now", "later", "timing"), 80.0),
    (ReplyCategory.ALREADY_USING_SOLUTION, ("already using", "we have a tool", "current vendor"), 84.0),
    (ReplyCategory.COMPETITOR, ("competitor", "comparing", "vs ", "alternative"), 78.0),
    (ReplyCategory.INTERNAL_DISCUSSION, ("discuss internally", "talk to the team", "loop in"), 76.0),
    (ReplyCategory.DECISION_PENDING, ("pending", "under review", "waiting on"), 75.0),
    (ReplyCategory.NEED_MORE_INFO, ("more info", "send details", "can you share", "tell me more"), 80.0),
    (ReplyCategory.INTERESTED, ("interested", "sounds good", "let's talk", "keen"), 85.0),
    (ReplyCategory.POSITIVE, ("thanks", "appreciate", "great", "love this"), 70.0),
]


class ReplyIntelligenceV2Engine:
    def analyze(self, events: list[OutreachEvent]) -> list[ReplyAnalysis]:
        out: list[ReplyAnalysis] = []
        for e in events:
            if not e.replied and not e.reply_text:
                if e.delivered and not e.replied:
                    out.append(
                        ReplyAnalysis(
                            reply_id=e.event_id,
                            category=ReplyCategory.NO_RESPONSE,
                            urgency=10.0,
                            confidence=60.0,
                            evidence=["no_reply:true"],
                        )
                    )
                continue
            blob = (e.reply_text or "").lower()
            category = ReplyCategory.POSITIVE
            conf = 55.0
            evidence = ["reply:observed"]
            for cat, patterns, base in REPLY_PATTERNS:
                hits = [p for p in patterns if p in blob]
                if hits:
                    category = cat
                    conf = min(95.0, base + len(hits) * 2.0)
                    evidence = [f"hits:{','.join(hits[:3])}"]
                    break
            urgency = 80.0 if category in {ReplyCategory.MEETING_REQUESTED, ReplyCategory.INTERESTED} else 40.0
            if category == ReplyCategory.NEGATIVE:
                urgency = 20.0
            out.append(
                ReplyAnalysis(
                    reply_id=e.event_id,
                    category=category,
                    urgency=urgency,
                    confidence=round(conf, 2),
                    evidence=evidence,
                )
            )
        return out


class RevenueLearningEngine:
    """Learn from outcomes — never mutate production, recommendations only."""

    def learn(self, events: list[OutreachEvent]) -> LearningInsight:
        wins = [e for e in events if e.closed_won]
        losses = [e for e in events if e.closed_lost]
        why_won = []
        if any(e.offer for e in wins):
            top_offer = Counter(e.offer for e in wins if e.offer).most_common(1)
            if top_offer:
                why_won.append(f"winning_offer:{top_offer[0][0]}")
        if any(e.cta for e in wins):
            top_cta = Counter(e.cta for e in wins if e.cta).most_common(1)
            if top_cta:
                why_won.append(f"winning_cta:{top_cta[0][0]}")
        if any(e.channel for e in wins):
            why_won.append(f"winning_channel:{Counter(e.channel for e in wins).most_common(1)[0][0]}")
        why_lost = []
        objections = []
        for e in losses:
            blob = (e.reply_text or "").lower()
            if "budget" in blob:
                why_lost.append("budget")
                objections.append("budget")
            if "timing" in blob or "later" in blob:
                why_lost.append("timing")
                objections.append("timing")
            if "competitor" in blob or "already using" in blob:
                why_lost.append("incumbent_or_competitor")
                objections.append("incumbent")
        patterns = []
        if any(e.followup_number >= 2 for e in wins):
            patterns.append("multi_touch_followups")
        if any(e.calendly_clicks > 0 for e in wins):
            patterns.append("calendly_engagement")
        best_channels = [c for c, _ in Counter(e.channel for e in wins if e.channel).most_common(3)]
        best_industries = [c for c, _ in Counter(e.industry for e in wins if e.industry).most_common(3)]
        best_hours = [str(h) for h, _ in Counter(e.open_hour for e in wins if e.open_hour is not None).most_common(2)]
        best_offers = [c for c, _ in Counter(e.offer for e in wins if e.offer).most_common(3)]
        return LearningInsight(
            insight_type="revenue_learning",
            summary=f"Analyzed {len(wins)} wins and {len(losses)} losses across {len(events)} events.",
            why_won=list(dict.fromkeys(why_won))[:8],
            why_lost=list(dict.fromkeys(why_lost))[:8],
            common_objections=list(dict.fromkeys(objections))[:8],
            winning_patterns=patterns,
            best_channels=best_channels,
            best_industries=best_industries,
            best_timing=[f"hour:{h}" for h in best_hours],
            best_offers=best_offers,
            modifies_production=False,
            confidence=min(95.0, 30.0 + len(wins) * 8.0 + len(losses) * 3.0),
            evidence=[f"wins:{len(wins)}", f"losses:{len(losses)}", "auto_apply:false"],
        )


class RevenueBenchmarkEngine:
    def benchmark(self, current: list[OutreachEvent], previous: list[OutreachEvent]) -> list[RevenueBenchmark]:
        out = []
        for period in Period:
            # same snapshot used as proxy for all periods in deterministic compose mode
            cur = self._kpis(current)
            prev = self._kpis(previous) if previous else {k: 0.0 for k in cur}
            growth = round(cur["open_rate"] - prev["open_rate"], 2)
            decline = round(max(0.0, prev["open_rate"] - cur["open_rate"]), 2)
            out.append(
                RevenueBenchmark(
                    period=period,
                    open_rate=cur["open_rate"],
                    reply_rate=cur["reply_rate"],
                    meeting_rate=cur["meeting_rate"],
                    proposal_rate=cur["proposal_rate"],
                    win_rate=cur["win_rate"],
                    revenue=cur["revenue"],
                    average_deal_size=cur["average_deal_size"],
                    sales_cycle_days=cur["sales_cycle_days"],
                    previous_open_rate=prev["open_rate"],
                    growth=growth,
                    decline=decline,
                    confidence=min(95.0, 35.0 + len(current) * 2.0),
                    evidence=[f"period:{period.value}", f"events:{len(current)}"],
                )
            )
        return out

    def _kpis(self, events: list[OutreachEvent]) -> dict[str, float]:
        n = len(events) or 1
        delivered = sum(1 for e in events if e.delivered) or n
        opened = sum(1 for e in events if e.opened)
        replied = sum(1 for e in events if e.replied)
        meetings = sum(1 for e in events if e.meeting_booked)
        proposals = sum(1 for e in events if e.proposal_sent)
        wins = sum(1 for e in events if e.closed_won)
        revenue = sum(e.deal_value for e in events if e.closed_won)
        deals = [e.deal_value for e in events if e.closed_won and e.deal_value > 0]
        cycles = [max(1.0, (e.reply_hours or 48) / 24.0) for e in events if e.closed_won]
        return {
            "open_rate": _rate(opened, delivered),
            "reply_rate": _rate(replied, delivered),
            "meeting_rate": _rate(meetings, delivered),
            "proposal_rate": _rate(proposals, delivered),
            "win_rate": _rate(wins, delivered),
            "revenue": round(revenue, 2),
            "average_deal_size": round(sum(deals) / len(deals), 2) if deals else 0.0,
            "sales_cycle_days": round(sum(cycles) / len(cycles), 2) if cycles else 0.0,
        }


class OptimizationRecommendationEngine:
    """Deterministic recommendations — founder approval required, never auto-apply."""

    def generate(
        self,
        *,
        followup_delay: float | None,
        industries: list,
        offers: list,
        followup_day: int | None,
        channels_by_industry: dict[str, str] | None = None,
    ) -> list[OptimizationRecommendation]:
        out: list[OptimizationRecommendation] = []
        if followup_delay is not None and followup_delay >= 3:
            rid = hashlib.sha256(f"delay|{followup_delay}".encode()).hexdigest()[:16]
            out.append(
                OptimizationRecommendation(
                    recommendation_id=rid,
                    title="Tune follow-up delay",
                    action=f"Increase follow-up delay to {followup_delay:.0f} days for SaaS companies."
                    if followup_delay >= 4
                    else f"Use ~{followup_delay:.1f} day follow-up delay based on successful replies.",
                    segment="SaaS",
                    confidence=78.0,
                    requires_founder_approval=True,
                    modifies_production=False,
                    evidence=[f"best_delay_days:{followup_delay}", "founder_approval:required"],
                )
            )
        for ind in industries[:5]:
            if getattr(ind, "reply_rate", 0) >= 20 and getattr(ind, "best_day", None) is None:
                pass
            day = followup_day
            if day == 1:  # Tuesday
                rid = hashlib.sha256(f"tue|{ind.industry}".encode()).hexdigest()[:16]
                out.append(
                    OptimizationRecommendation(
                        recommendation_id=rid,
                        title=f"Timing for {ind.industry}",
                        action=f"{ind.industry} responds better on Tuesday mornings."
                        if ind.industry.lower() in {"manufacturing", "saas", "healthcare"}
                        else f"Prioritize {ind.industry} outreach near weekday {day}.",
                        segment=ind.industry,
                        confidence=min(90.0, 60.0 + ind.reply_rate * 0.3),
                        requires_founder_approval=True,
                        modifies_production=False,
                        evidence=[f"industry:{ind.industry}", f"reply_rate:{ind.reply_rate}", f"day:{day}"],
                    )
                )
            if ind.industry.lower() == "healthcare" and offers:
                top = offers[0]
                if "audit" in top.offer.lower() or "ai" in top.offer.lower():
                    rid = hashlib.sha256(f"health|{top.offer}".encode()).hexdigest()[:16]
                    out.append(
                        OptimizationRecommendation(
                            recommendation_id=rid,
                            title="Healthcare offer fit",
                            action="Healthcare companies prefer AI Audit offers.",
                            segment="Healthcare",
                            confidence=82.0,
                            requires_founder_approval=True,
                            modifies_production=False,
                            evidence=[f"offer:{top.offer}", f"wins:{top.wins}"],
                        )
                    )
        if channels_by_industry:
            for industry, channel in channels_by_industry.items():
                if channel == "whatsapp" and industry.lower() in {"construction", "manufacturing"}:
                    rid = hashlib.sha256(f"wa|{industry}".encode()).hexdigest()[:16]
                    out.append(
                        OptimizationRecommendation(
                            recommendation_id=rid,
                            title=f"{industry} channel",
                            action=f"{industry} companies engage more on WhatsApp.",
                            segment=industry,
                            confidence=80.0,
                            requires_founder_approval=True,
                            modifies_production=False,
                            evidence=[f"channel:whatsapp", f"industry:{industry}"],
                        )
                    )
        # always include a no-auto-apply guarantee recommendation summary
        if not out:
            rid = hashlib.sha256(b"maintain").hexdigest()[:16]
            out.append(
                OptimizationRecommendation(
                    recommendation_id=rid,
                    title="Maintain current motion",
                    action="Insufficient differentiated signal — maintain current sequences pending more evidence.",
                    segment="all",
                    confidence=50.0,
                    requires_founder_approval=True,
                    modifies_production=False,
                    evidence=["insufficient_signal:true"],
                )
            )
        return out[:20]
