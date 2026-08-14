from __future__ import annotations

import re

from decision_discovery.models.types import DecisionRole

_ROLE_PATTERNS: tuple[tuple[str, DecisionRole, str, int], ...] = (
    (r"\b(co[- ]?founder|founder)\b", DecisionRole.FOUNDER, "Leadership", 100),
    (r"\bchief executive officer\b|\bceo\b", DecisionRole.CEO, "Leadership", 98),
    (r"\bchief technology officer\b|\bcto\b", DecisionRole.CTO, "Engineering", 95),
    (r"\bchief operating officer\b|\bcoo\b", DecisionRole.COO, "Operations", 94),
    (r"\bhead of engineering\b|\svp[, ]? engineering\b", DecisionRole.HEAD_OF_ENGINEERING, "Engineering", 90),
    (r"\bengineering manager\b", DecisionRole.ENGINEERING_MANAGER, "Engineering", 82),
    (
        r"\bhead of (customer )?support\b|\bsupport (director|head|lead)\b|\bvp[, ]? support\b",
        DecisionRole.HEAD_OF_CUSTOMER_SUPPORT,
        "Support",
        88,
    ),
    (r"\bsupport manager\b", DecisionRole.SUPPORT_MANAGER, "Support", 78),
    (r"\bhead of operations\b|\boperations (director|head|lead)\b", DecisionRole.HEAD_OF_OPERATIONS, "Operations", 88),
    (r"\bhead of marketing\b|\bmarketing (director|head|lead)\b|\bcmo\b", DecisionRole.MARKETING_HEAD, "Marketing", 86),
    (r"\bhead of sales\b|\bsales (director|head|lead)\b|\bcro\b", DecisionRole.SALES_HEAD, "Sales", 86),
    (r"\bproduct manager\b|\bhead of product\b|\bcpo\b", DecisionRole.PRODUCT_MANAGER, "Product", 84),
    (r"\bai (lead|head|director)\b|\bhead of ai\b|\bml (lead|head)\b", DecisionRole.AI_LEAD, "AI", 87),
    (r"\binnovation (lead|head|director)\b", DecisionRole.INNOVATION_LEAD, "Innovation", 80),
)

_PLACEHOLDER_NAME_RE = re.compile(
    r"^(unknown|n/?a|team|company|the company|contact|support|sales|hello)\b",
    re.I,
)
_CORPORATE_TOKENS = frozenset(
    {
        "inc",
        "llc",
        "ltd",
        "corp",
        "corporation",
        "company",
        "companies",
        "logistics",
        "technologies",
        "technology",
        "systems",
        "solutions",
        "software",
        "labs",
        "group",
        "holdings",
        "ventures",
        "partners",
        "industries",
    }
)


def normalize_role(role_raw: str) -> tuple[DecisionRole, str, int] | None:
    lowered = role_raw.strip().lower()
    if not lowered:
        return None
    for pattern, role, department, seniority in _ROLE_PATTERNS:
        if re.search(pattern, lowered, flags=re.I):
            return role, department, seniority
    return None


def is_plausible_person_name(name: str) -> bool:
    cleaned = name.strip()
    if len(cleaned) < 3 or len(cleaned) > 80:
        return False
    if _PLACEHOLDER_NAME_RE.search(cleaned):
        return False
    tokens = [token for token in re.split(r"\s+", cleaned) if token]
    if any(token.lower().strip(".,") in _CORPORATE_TOKENS for token in tokens):
        return False
    if len(tokens) < 2:
        # Allow single-token names only when clearly capitalized proper nouns.
        return cleaned[:1].isupper() and cleaned.replace("-", "").isalpha() and len(cleaned) >= 4
    return all(token[:1].isupper() for token in tokens[:3])


def department_for_role(role: str) -> str:
    normalized = normalize_role(role)
    if normalized is not None:
        return normalized[1]
    lowered = role.lower()
    if "support" in lowered:
        return "Support"
    if "market" in lowered:
        return "Marketing"
    if "sales" in lowered:
        return "Sales"
    if "engineer" in lowered or "cto" in lowered or "ai" in lowered:
        return "Engineering"
    if "operat" in lowered or "coo" in lowered:
        return "Operations"
    if "product" in lowered:
        return "Product"
    return "Leadership"
