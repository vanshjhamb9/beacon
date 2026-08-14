from __future__ import annotations

import re

from lead_enrichment.models.types import (
    EnrichmentOpportunityInput,
    EnrichmentSourceType,
    JobEntry,
    TeamInsights,
    WebsiteFetchResult,
)

_JOB_LINE_RE = re.compile(
    r"\b((?:Senior |Staff |Lead |Principal )?(?:Software|Backend|Frontend|Full[- ]Stack|Data|ML|Product|Support|Sales|Marketing|Operations|Engineering) (?:Engineer|Manager|Designer|Analyst|Lead|Specialist|Director))\b",
    re.I,
)


class JobsExtractor:
    def extract(
        self,
        item: EnrichmentOpportunityInput,
        website: WebsiteFetchResult | None,
        people_count: int,
    ) -> tuple[list[JobEntry], TeamInsights]:
        jobs: list[JobEntry] = []
        recent_hires: list[str] = []
        seen: set[str] = set()

        hiring_pattern = str(item.context_intelligence.get("hiring_pattern") or "")
        if hiring_pattern:
            recent_hires.append(hiring_pattern)

        if website:
            for page in website.pages:
                if page.page_type not in {"careers", "homepage", "about", "team"}:
                    continue
                for match in _JOB_LINE_RE.finditer(page.text):
                    title = match.group(1).strip()
                    key = title.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    jobs.append(
                        JobEntry(
                            title=title,
                            department=self._department(title),
                            url=page.url if page.page_type == "careers" else None,
                            confidence=78.0 if page.page_type == "careers" else 55.0,
                            source=EnrichmentSourceType.COMPANY_WEBSITE,
                            source_url=page.url,
                        )
                    )
                if "hiring" in page.text.lower() or "we're hiring" in page.text.lower():
                    recent_hires.append(f"Hiring signal on {page.page_type} page")

        for signal in item.opportunity_evidence:
            summary = str(signal.get("summary") or "")
            category = str(signal.get("category") or "").lower()
            if "hir" in category or "hir" in summary.lower():
                recent_hires.append(summary[:160])

        eng = sum(1 for job in jobs if job.department == "Engineering")
        support = sum(1 for job in jobs if job.department == "Support")
        ops = sum(1 for job in jobs if job.department == "Operations")
        leadership = max(people_count, 1) if people_count else (1 if jobs else None)

        trend = None
        if len(jobs) >= 3:
            trend = "Active hiring across multiple functions"
        elif len(jobs) == 1:
            trend = "Selective hiring"
        elif hiring_pattern:
            trend = hiring_pattern

        insights = TeamInsights(
            leadership_team_size=leadership,
            engineering_team_estimate=eng or None,
            support_team_estimate=support or None,
            operations_team_estimate=ops or None,
            recent_hires=list(dict.fromkeys(recent_hires))[:10],
            open_positions=[job.title for job in jobs],
            hiring_trends=trend,
        )
        return jobs, insights

    def _department(self, title: str) -> str:
        lowered = title.lower()
        if "support" in lowered:
            return "Support"
        if "operat" in lowered:
            return "Operations"
        if "market" in lowered or "sales" in lowered:
            return "Go-To-Market"
        if "product" in lowered or "design" in lowered:
            return "Product"
        return "Engineering"
