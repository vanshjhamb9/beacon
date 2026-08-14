from __future__ import annotations

from collections import Counter, defaultdict

from revenue_optimization.models.types import CTAPerformance, FollowupPattern, OutreachEvent


def _rate(num: int, den: int) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


class CTAIntelligenceEngine:
    def analyze(self, events: list[OutreachEvent]) -> list[CTAPerformance]:
        buckets: dict[str, list[OutreachEvent]] = defaultdict(list)
        for e in events:
            if e.cta:
                buckets[e.cta].append(e)
        out: list[CTAPerformance] = []
        for cta, items in buckets.items():
            n = len(items)
            clicks = sum(e.calendly_clicks + e.website_visits for e in items)
            replies = sum(1 for e in items if e.replied)
            meetings = sum(1 for e in items if e.meeting_booked)
            deals = sum(1 for e in items if e.closed_won)
            revenue = sum(e.deal_value for e in items if e.closed_won)
            ctr = _rate(clicks, n)
            score = ctr * 0.25 + _rate(replies, n) * 0.25 + _rate(meetings, n) * 0.25 + _rate(deals, n) * 0.25
            out.append(
                CTAPerformance(
                    cta=cta,
                    sends=n,
                    ctr=ctr,
                    replies=replies,
                    meetings=meetings,
                    deals=deals,
                    revenue=round(revenue, 2),
                    score=round(score, 2),
                    confidence=min(95.0, 35.0 + n * 5.0),
                    evidence=[f"cta:{cta}", f"sends:{n}"],
                )
            )
        out.sort(key=lambda x: (-x.score, x.cta))
        return out


class FollowupIntelligenceEngine:
    def analyze(self, events: list[OutreachEvent]) -> FollowupPattern:
        success = [e for e in events if e.replied or e.meeting_booked or e.closed_won]
        if not success:
            success = events
        day_counts = Counter(e.open_weekday for e in success if e.open_weekday is not None)
        hour_counts = Counter(e.open_hour for e in success if e.open_hour is not None)
        tz_counts = Counter(e.timezone for e in success if e.timezone)
        delays = [e.delay_days for e in success if e.delay_days is not None]
        followups = [e.followup_number for e in success]
        sequences = [e.sequence_length for e in success]

        industry_timing: dict[str, dict] = {}
        for ind, items in self._group(success, "industry").items():
            industry_timing[ind] = {
                "best_day": self._mode([e.open_weekday for e in items if e.open_weekday is not None]),
                "best_hour": self._mode([e.open_hour for e in items if e.open_hour is not None]),
            }
        size_timing: dict[str, dict] = {}
        for size, items in self._group(success, "company_size_band").items():
            size_timing[size] = {
                "best_day": self._mode([e.open_weekday for e in items if e.open_weekday is not None]),
                "best_hour": self._mode([e.open_hour for e in items if e.open_hour is not None]),
            }
        founder_items = [e for e in success if e.founder_actor]
        founder_timing = {
            "best_day": self._mode([e.open_weekday for e in founder_items if e.open_weekday is not None]),
            "best_hour": self._mode([e.open_hour for e in founder_items if e.open_hour is not None]),
        }
        return FollowupPattern(
            best_day=day_counts.most_common(1)[0][0] if day_counts else None,
            best_hour=hour_counts.most_common(1)[0][0] if hour_counts else None,
            best_timezone=tz_counts.most_common(1)[0][0] if tz_counts else None,
            best_delay_days=round(sum(delays) / len(delays), 2) if delays else None,
            best_followup_count=int(round(sum(followups) / len(followups))) if followups else None,
            best_sequence_length=int(round(sum(sequences) / len(sequences))) if sequences else None,
            industry_timing=industry_timing,
            company_size_timing=size_timing,
            founder_timing=founder_timing,
            confidence=min(95.0, 25.0 + len(success) * 3.0),
            evidence=[f"success_events:{len(success)}", f"days:{dict(day_counts)}"],
        )

    def _group(self, events: list[OutreachEvent], attr: str) -> dict[str, list[OutreachEvent]]:
        out: dict[str, list[OutreachEvent]] = defaultdict(list)
        for e in events:
            key = getattr(e, attr)
            if key:
                out[str(key)].append(e)
        return out

    def _mode(self, values: list[int]) -> int | None:
        if not values:
            return None
        return Counter(values).most_common(1)[0][0]
