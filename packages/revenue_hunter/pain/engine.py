from __future__ import annotations

from revenue_hunter.models.types import PainPoint, RevenueHunterInput


# Canonical pain catalog with detection patterns (deterministic)
PAIN_CATALOG: list[dict[str, object]] = [
    {
        "problem": "Growing support",
        "category": "support",
        "patterns": ["growing support", "support growth", "support team", "ticket volume", "customer support"],
        "roles": ["support", "cx", "customer success", "helpdesk"],
    },
    {
        "problem": "Hiring operations",
        "category": "ops",
        "patterns": ["hiring operations", "ops hiring", "operations headcount", "backfill ops"],
        "roles": ["operations", "ops", "coo", "business operations"],
    },
    {
        "problem": "Manual workflows",
        "category": "automation",
        "patterns": ["manual workflows", "manual process", "repeated manual", "spreadsheet ops", "copy paste"],
        "roles": ["operations analyst", "process"],
    },
    {
        "problem": "Poor website",
        "category": "web",
        "patterns": ["poor website", "outdated website", "weak website", "ugly site", "broken site"],
        "roles": ["web", "marketing"],
    },
    {
        "problem": "No automation",
        "category": "automation",
        "patterns": ["no automation", "lack of automation", "not automated", "still manual"],
        "roles": ["automation", "rpa"],
    },
    {
        "problem": "Scaling issues",
        "category": "growth",
        "patterns": ["scaling issues", "scaling", "can't scale", "growth bottleneck", "capacity"],
        "roles": ["growth", "scaling"],
    },
    {
        "problem": "Old technology",
        "category": "tech",
        "patterns": ["old technology", "legacy", "outdated tech", "tech debt", "modernization"],
        "roles": ["engineer", "cto", "platform"],
    },
    {
        "problem": "High support cost",
        "category": "support",
        "patterns": ["high support cost", "support cost", "expensive support", "cost of support"],
        "roles": ["support", "cx"],
    },
    {
        "problem": "Poor conversion",
        "category": "growth",
        "patterns": ["poor conversion", "low conversion", "conversion rate", "checkout drop"],
        "roles": ["growth", "marketing", "product"],
    },
]


class PainPointEngine:
    """Extract top problems with required evidence."""

    def analyze(self, item: RevenueHunterInput, *, limit: int = 5) -> list[PainPoint]:
        blob = " ".join(
            [
                " ".join(item.pains),
                " ".join(item.signals),
                " ".join(item.goals),
                " ".join(item.growth_signals),
                " ".join(item.hiring_roles),
                " ".join(item.news),
            ]
        ).lower()
        roles_blob = " ".join(item.hiring_roles).lower()
        found: list[PainPoint] = []

        for entry in PAIN_CATALOG:
            patterns = [str(p).lower() for p in entry["patterns"]]  # type: ignore[index]
            roles = [str(r).lower() for r in entry["roles"]]  # type: ignore[index]
            evidence: list[str] = []
            hits = 0
            for pattern in patterns:
                if pattern in blob:
                    hits += 1
                    evidence.append(f"signal:{pattern}")
            role_hits = sum(1 for r in roles if r in roles_blob)
            if role_hits:
                evidence.append(f"hiring_roles:{role_hits}")
                hits += role_hits
            if item.hiring_count >= 5 and entry["category"] in {"support", "ops"}:
                evidence.append(f"hiring_count:{item.hiring_count}")
                hits += 1
            if hits == 0:
                continue
            confidence = min(100.0, 40.0 + hits * 12.0 + min(20.0, item.opportunity_score * 0.15))
            found.append(
                PainPoint(
                    problem=str(entry["problem"]),
                    confidence=round(confidence, 4),
                    evidence=evidence,
                    category=str(entry["category"]),
                )
            )

        found.sort(key=lambda p: (-p.confidence, p.problem))
        return found[:limit]
