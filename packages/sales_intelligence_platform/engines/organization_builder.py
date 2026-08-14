"""Organization Builder - Build company organization structure."""

from __future__ import annotations

from packages.sales_intelligence_platform.models import Account, DecisionMaker


def build_organization(account: Account) -> dict:
    """Build organizational structure from decision makers."""
    org: dict[str, list[dict]] = {
        "leadership": [],
        "operations": [],
        "technology": [],
        "growth": [],
        "support": [],
        "unknown": [],
    }

    for dm in account.decision_makers:
        role_lower = dm.normalized_role.lower()
        entry = {
            "name": dm.name,
            "role": dm.normalized_role,
            "confidence": dm.confidence,
            "source": dm.source,
        }

        if any(kw in role_lower for kw in ("founder", "ceo", "director", "owner", "managing")):
            org["leadership"].append(entry)
        elif any(kw in role_lower for kw in ("operation", "store", "inventory")):
            org["operations"].append(entry)
        elif any(kw in role_lower for kw in ("technology", "engineering", "cto", "tech")):
            org["technology"].append(entry)
        elif any(kw in role_lower for kw in ("growth", "marketing", "digital")):
            org["growth"].append(entry)
        elif any(kw in role_lower for kw in ("support", "customer")):
            org["support"].append(entry)
        else:
            org["unknown"].append(entry)

    return org
