from __future__ import annotations

from account_journey.models.types import AccountJourneyInput, CampaignAnalytics, CampaignAnalyticsSlice


class GlobalCampaignAnalyticsEngine:
    def analyze(self, item: AccountJourneyInput) -> CampaignAnalytics:
        cohort = list(item.cohort_accounts) or [
            {
                "country": item.country,
                "industry": item.industry,
                "company_size": item.company_size,
                "technology": (item.technologies[0] if item.technologies else None),
                "service": item.service,
                "campaign": item.campaign_name,
                "dm_role": (item.decision_makers[0].get("title") if item.decision_makers else None),
                "replied": item.replied,
                "meeting": item.meeting_scheduled,
                "proposal": item.proposal_requested,
                "won": item.won,
                "revenue": 35000.0 if item.won else (item.probability * 400.0),
            }
        ]
        return CampaignAnalytics(
            by_country=self._slice(cohort, "country"),
            by_industry=self._slice(cohort, "industry"),
            by_company_size=self._slice(cohort, "company_size"),
            by_technology=self._slice(cohort, "technology"),
            by_service=self._slice(cohort, "service"),
            by_campaign=self._slice(cohort, "campaign"),
            by_decision_maker_role=self._slice(cohort, "dm_role"),
            evidence=[f"cohort:{len(cohort)}", "compose:existing_signals"],
        )

    def _slice(self, cohort: list[dict], dimension: str) -> list[CampaignAnalyticsSlice]:
        buckets: dict[str, list[dict]] = {}
        for row in cohort:
            key = str(row.get(dimension) or "unknown")
            buckets.setdefault(key, []).append(row)
        out: list[CampaignAnalyticsSlice] = []
        for key, rows in buckets.items():
            n = max(1, len(rows))
            out.append(
                CampaignAnalyticsSlice(
                    dimension=dimension,
                    key=key,
                    reply_pct=round(sum(1 for r in rows if r.get("replied")) / n * 100.0, 2),
                    meeting_pct=round(sum(1 for r in rows if r.get("meeting")) / n * 100.0, 2),
                    proposal_pct=round(sum(1 for r in rows if r.get("proposal")) / n * 100.0, 2),
                    close_pct=round(sum(1 for r in rows if r.get("won")) / n * 100.0, 2),
                    revenue=round(sum(float(r.get("revenue") or 0) for r in rows), 2),
                    accounts=len(rows),
                    evidence=[f"dim:{dimension}", f"key:{key}", f"n:{len(rows)}"],
                )
            )
        out.sort(key=lambda s: (-s.revenue, -s.reply_pct, s.key))
        return out[:12]
