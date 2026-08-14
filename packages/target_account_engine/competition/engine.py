from __future__ import annotations

from target_account_engine.models.types import EngineScore, TargetAccountInput


_VENDOR_CATEGORIES = {
    "agency": ("agency", "digital agency", "marketing agency"),
    "crm": ("salesforce", "hubspot", "pipedrive", "zoho"),
    "support": ("zendesk", "intercom", "freshdesk", "gorgias"),
    "ai": ("openai", "jasper", "copy.ai", "chatgpt"),
    "automation": ("zapier", "make.com", "n8n", "uipath"),
    "website": ("webflow", "wix", "squarespace", "wordpress agency"),
}


class CompetitionEngine:
    """Higher score = larger opportunity gap (weaker incumbent coverage)."""

    def score(self, item: TargetAccountInput) -> EngineScore:
        vendors = [v.lower() for v in item.vendors] + [t.lower() for t in item.technologies]
        present: dict[str, list[str]] = {}
        for category, needles in _VENDOR_CATEGORIES.items():
            hits = [n for n in needles if any(n in v for v in vendors)]
            if hits:
                present[category] = hits

        covered = len(present)
        gap = max(0, 6 - covered)
        # Start high (open field), reduce when dense vendor stack exists
        score = 40.0 + gap * 10.0
        if "ai" not in present and "automation" not in present:
            score += 12.0
        if "support" in present and "ai" not in present:
            score += 10.0  # support tools without AI = COMAI/AI wedge
        if covered >= 5:
            score -= 15.0
        score = max(0.0, min(100.0, score))
        evidence = [f"Vendor categories present: {', '.join(sorted(present)) or 'none'}"]
        for category, hits in present.items():
            evidence.append(f"{category}: {', '.join(hits[:3])}")
        evidence.append(f"Opportunity gap categories open: {gap}")
        return EngineScore(
            score=round(score, 2),
            explanation=(
                f"Competition gap {score:.1f}/100 — {covered} vendor categories present, "
                f"{gap} open wedges."
            ),
            evidence=evidence,
            details={"present_categories": present, "gap": gap},
        )
