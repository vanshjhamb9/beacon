from __future__ import annotations

from collections import Counter, defaultdict

from revenue_optimization.models.types import EmailMetrics, OutreachEvent, SubjectPerformance


def _rate(num: int, den: int) -> float:
    return round(100.0 * num / den, 2) if den else 0.0


class EmailPerformanceEngine:
    def analyze(self, events: list[OutreachEvent]) -> EmailMetrics:
        email = [e for e in events if e.channel == "email"]
        delivered = sum(1 for e in email if e.delivered)
        opened = sum(1 for e in email if e.opened)
        multi = sum(1 for e in email if e.open_count >= 2)
        open_times = [e.open_hour for e in email if e.open_hour is not None]
        devices = Counter(e.open_device for e in email if e.open_device)
        countries = Counter(e.open_country for e in email if e.open_country)
        replies = sum(1 for e in email if e.replied)
        reply_times = [float(e.reply_hours) for e in email if e.reply_hours is not None]
        timeline = []
        for e in email[:50]:
            timeline.append(
                {
                    "event_id": e.event_id,
                    "company_name": e.company_name,
                    "delivered": e.delivered,
                    "opened": e.opened,
                    "replied": e.replied,
                    "evidence": list(e.evidence),
                }
            )
        conf = min(95.0, 30.0 + len(email) * 2.0)
        return EmailMetrics(
            delivered=delivered,
            opened=opened,
            multiple_opens=multi,
            open_times=open_times,
            open_devices=dict(devices),
            open_countries=dict(countries),
            attachment_downloads=sum(e.attachment_downloads for e in email),
            video_views=sum(e.video_views for e in email),
            calendly_clicks=sum(e.calendly_clicks for e in email),
            website_visits=sum(e.website_visits for e in email),
            reply_times_hours=reply_times,
            bounce=sum(1 for e in email if e.bounced),
            spam=sum(1 for e in email if e.spam),
            unsubscribe=sum(1 for e in email if e.unsubscribed),
            open_rate=_rate(opened, delivered),
            reply_rate=_rate(replies, delivered),
            confidence=round(conf, 2),
            evidence=[f"emails:{len(email)}", f"delivered:{delivered}"],
            timeline=timeline,
        )


class SubjectLineIntelligenceEngine:
    def rank(self, events: list[OutreachEvent]) -> list[SubjectPerformance]:
        buckets: dict[str, list[OutreachEvent]] = defaultdict(list)
        for e in events:
            if e.subject:
                buckets[e.subject].append(e)
        rows: list[SubjectPerformance] = []
        for subject, items in buckets.items():
            n = len(items)
            opened = sum(1 for e in items if e.opened)
            replied = sum(1 for e in items if e.replied)
            meetings = sum(1 for e in items if e.meeting_booked)
            proposals = sum(1 for e in items if e.proposal_sent)
            wins = sum(1 for e in items if e.closed_won)
            revenue = sum(e.deal_value for e in items if e.closed_won)
            score = (
                _rate(opened, n) * 0.2
                + _rate(replied, n) * 0.25
                + _rate(meetings, n) * 0.2
                + _rate(proposals, n) * 0.15
                + _rate(wins, n) * 0.2
                + min(20.0, revenue * 0.01)
            )
            rows.append(
                (
                    score,
                    SubjectPerformance(
                        subject=subject,
                        sends=n,
                        open_rate=_rate(opened, n),
                        reply_rate=_rate(replied, n),
                        meeting_rate=_rate(meetings, n),
                        proposal_rate=_rate(proposals, n),
                        close_rate=_rate(wins, n),
                        revenue_generated=round(revenue, 2),
                        rank=0,
                        confidence=min(95.0, 40.0 + n * 5.0),
                        evidence=[f"sends:{n}", f"score:{round(score, 2)}"],
                    ),
                )
            )
        rows.sort(key=lambda x: (-x[0], x[1].subject))
        return [r.model_copy(update={"rank": i, "evidence": r.evidence + [f"rank:{i}"]}) for i, (_, r) in enumerate(rows, start=1)]
