"""Role Classifier Engine - Normalize and classify roles."""

from __future__ import annotations

import re

from packages.sales_intelligence_platform.models import DecisionMaker

ROLE_MAP: dict[str, tuple[str, int]] = {
    "founder": ("Founder", 1),
    "co-founder": ("Co-Founder", 2),
    "cofounder": ("Co-Founder", 2),
    "ceo": ("CEO", 3),
    "chief executive": ("CEO", 3),
    "managing director": ("Managing Director", 4),
    "md": ("Managing Director", 4),
    "director": ("Director", 5),
    "head of ecommerce": ("Head of Ecommerce", 6),
    "ecommerce head": ("Head of Ecommerce", 6),
    "ecommerce manager": ("Head of Ecommerce", 6),
    "head of operations": ("Head of Operations", 7),
    "operations head": ("Head of Operations", 7),
    "coo": ("Head of Operations", 7),
    "head of customer success": ("Head of Customer Success", 8),
    "head of growth": ("Head of Growth", 9),
    "growth head": ("Head of Growth", 9),
    "head of marketing": ("Head of Marketing", 10),
    "marketing head": ("Head of Marketing", 10),
    "cmo": ("Head of Marketing", 10),
    "head of technology": ("Head of Technology", 11),
    "technology head": ("Head of Technology", 11),
    "cto": ("Head of Technology", 11),
    "engineering lead": ("Engineering Lead", 12),
    "tech lead": ("Engineering Lead", 12),
    "product manager": ("Product Manager", 13),
    "customer support manager": ("Customer Support Manager", 14),
    "support manager": ("Customer Support Manager", 14),
    "operations manager": ("Operations Manager", 15),
    "store owner": ("Store Owner", 16),
    "owner": ("Store Owner", 16),
}


def classify_roles(decision_makers: list[DecisionMaker]) -> list[DecisionMaker]:
    """Normalize and classify roles for all decision makers."""
    for dm in decision_makers:
        role_text = dm.normalized_role.lower() if dm.normalized_role else ""
        if not role_text:
            continue

        for pattern, (normalized, rank) in ROLE_MAP.items():
            if pattern in role_text:
                dm.normalized_role = normalized
                dm.seniority_rank = rank
                break

    # Sort by seniority
    decision_makers.sort(key=lambda dm: dm.seniority_rank)
    return decision_makers
