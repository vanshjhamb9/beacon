"""Deterministic score breakdown — explains existing scores; does not rescore."""

from __future__ import annotations

from typing import Any


# Fixed attribution weights for explainability of an existing score.
# These allocate an already-computed score into labeled components.
COMPONENT_CATALOG: tuple[tuple[str, str, int], ...] = (
    ("signal_quality", "Signal Quality", 15),
    ("founder_found", "Founder Found", 20),
    ("website_verified", "Website Verified", 15),
    ("business_email", "Business Email", 20),
    ("recent_hiring", "Recent Hiring", 10),
    ("funding", "Funding", 10),
    ("industry_match", "Industry Match", 9),
)


def explain_score(
    *,
    total_score: float,
    facts: dict[str, Any] | None = None,
    existing_components: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Explain an existing score as additive labeled parts.

    If `existing_components` were recorded in lead_score_breakdown, prefer those.
    Otherwise attribute from boolean facts without inventing a new scoring model —
    components that lack evidence are shown as +0.
    """
    facts = facts or {}
    if existing_components:
        parts = [
            {
                "key": c.get("component_key") or c.get("key") or "",
                "label": c.get("label") or str(c.get("component_key") or "Component"),
                "points": float(c.get("points") or 0),
                "present": bool(c.get("present", True)),
                "evidence": list(c.get("evidence") or []),
            }
            for c in existing_components
        ]
        computed = round(sum(p["points"] for p in parts), 2)
        return {
            "total": float(total_score),
            "explained_total": computed,
            "components": parts,
            "source": "recorded",
        }

    presence = {
        "signal_quality": bool(facts.get("has_signal") or facts.get("signal_at")),
        "founder_found": bool(facts.get("has_founder") or facts.get("decision_maker_at") or facts.get("founder")),
        "website_verified": bool(facts.get("has_website") or facts.get("website_at") or facts.get("domain")),
        "business_email": bool(facts.get("has_email") or facts.get("email_at") or facts.get("business_email")),
        "recent_hiring": bool(facts.get("has_hiring") or facts.get("hiring")),
        "funding": bool(facts.get("has_funding") or facts.get("funding") or facts.get("yc")),
        "industry_match": bool(facts.get("has_industry") or facts.get("industry")),
    }

    parts: list[dict[str, Any]] = []
    raw_sum = 0.0
    for key, label, max_pts in COMPONENT_CATALOG:
        present = presence.get(key, False)
        pts = float(max_pts) if present else 0.0
        raw_sum += pts
        evidence: list[str] = []
        if present:
            if key == "founder_found" and facts.get("founder"):
                evidence.append(str(facts["founder"]))
            if key == "business_email" and facts.get("business_email"):
                evidence.append(str(facts["business_email"]))
            if key == "website_verified" and facts.get("domain"):
                evidence.append(str(facts["domain"]))
            if key == "industry_match" and facts.get("industry"):
                evidence.append(str(facts["industry"]))
        parts.append(
            {
                "key": key,
                "label": label,
                "points": pts,
                "present": present,
                "evidence": evidence,
            }
        )

    # Scale attributed points to match the existing total (explainability, not re-score).
    target = float(total_score or 0)
    if raw_sum > 0 and target > 0:
        scale = target / raw_sum
        for part in parts:
            part["points"] = round(float(part["points"]) * scale, 2)
        # Fix rounding drift on last present component
        drift = round(target - sum(float(p["points"]) for p in parts), 2)
        for part in reversed(parts):
            if part["present"]:
                part["points"] = round(float(part["points"]) + drift, 2)
                break

    return {
        "total": target,
        "explained_total": round(sum(float(p["points"]) for p in parts), 2),
        "components": parts,
        "source": "attributed",
    }
