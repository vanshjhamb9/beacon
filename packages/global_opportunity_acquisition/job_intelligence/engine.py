from __future__ import annotations

from global_opportunity_acquisition.models.types import HiringInsight

ROLE_BUCKETS: list[tuple[str, tuple[str, ...]]] = [
    ("engineering_expansion", ("engineer", "developer", "backend", "frontend", "devops", "sre")),
    ("ai_investment", ("machine learning", "ml engineer", "ai engineer", "llm", "data scientist")),
    ("product_investment", ("product manager", "product designer", "ux")),
    ("sales_expansion", ("account executive", "sales", "sdr", "bdr")),
    ("support_expansion", ("customer support", "success", "support engineer")),
    ("marketing_expansion", ("marketing", "growth", "content", "demand gen")),
]


class JobIntelligenceEngine:
    def analyze(self, job_titles: list[str]) -> HiringInsight:
        blob = " ".join(job_titles).lower()
        scores: dict[str, float] = {k: 0.0 for k, _ in ROLE_BUCKETS}
        matched_roles: list[str] = []
        for key, patterns in ROLE_BUCKETS:
            hits = [p for p in patterns if p in blob]
            if hits:
                scores[key] = min(100.0, 40.0 + len(hits) * 15.0)
                matched_roles.extend(hits[:3])
        growth = min(100.0, len(job_titles) * 12.0 + sum(scores.values()) * 0.05)
        return HiringInsight(
            growth=round(growth, 2),
            engineering_expansion=round(scores["engineering_expansion"], 2),
            ai_investment=round(scores["ai_investment"], 2),
            product_investment=round(scores["product_investment"], 2),
            sales_expansion=round(scores["sales_expansion"], 2),
            support_expansion=round(scores["support_expansion"], 2),
            marketing_expansion=round(scores["marketing_expansion"], 2),
            roles=list(dict.fromkeys(matched_roles))[:12],
            evidence=[f"jobs:{len(job_titles)}", f"growth:{growth}"],
        )
