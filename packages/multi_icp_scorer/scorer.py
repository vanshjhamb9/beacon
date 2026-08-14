"""Multi-ICP Scorer for Beacon.

Scores a company against all three Inowix ICPs:
- COMAI (AI automation for ecommerce)
- SaaS Development (product engineering)
- Custom Software (business solutions)

Returns separate scores + primary/secondary routing.
Does NOT merge into one opaque number.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from packages.intent_engine.detector import classify_overall_intent, detect_intent
from packages.intent_engine.service_matcher import match_services
from packages.opportunity_intelligence.canonical import (
    BusinessUnit,
    ICPScore,
    EvidenceConfidence,
    EvidenceRecord,
    IntentLevel,
    ServiceMatch,
)


@dataclass
class ICPRule:
    """A single ICP evaluation rule."""
    dimension: str  # ecommerce_presence, whatsapp_usage, tech_stack, etc.
    evidence_keywords: list[str]
    score_contribution: float  # 0-100
    evidence_confidence: EvidenceConfidence
    description: str


# ============================================================
# COMAI RULES (AI automation for ecommerce brands)
# ============================================================

COMAI_RULES: list[ICPRule] = [
    ICPRule(
        dimension="ecommerce_presence",
        evidence_keywords=["shopify", "woocommerce", "bigcommerce", "ecommerce store",
                           "online store", "d2c", "online shop", "ecommerce brand"],
        score_contribution=20,
        evidence_confidence=EvidenceConfidence.HIGH,
        description="Has ecommerce presence",
    ),
    ICPRule(
        dimension="customer_support_need",
        evidence_keywords=["customer support", "customer service", "support team",
                           "customer queries", "customer complaints"],
        score_contribution=18,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Has customer support operations",
    ),
    ICPRule(
        dimension="digital_presence",
        evidence_keywords=["instagram", "facebook", "social media", "digital marketing",
                           "online presence", "social media following"],
        score_contribution=12,
        evidence_confidence=EvidenceConfidence.HIGH,
        description="Has digital presence",
    ),
    ICPRule(
        dimension="growth_stage",
        evidence_keywords=["funded", "raised", "expanding", "scaling", "growing",
                           "new launch", "series"],
        score_contribution=10,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Growth stage company",
    ),
    ICPRule(
        dimension="manual_operations",
        evidence_keywords=["manual", "repetitive", "time-consuming", "bottleneck",
                           "inefficient", "struggling"],
        score_contribution=15,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Has manual operations",
    ),
    ICPRule(
        dimension="product_range",
        evidence_keywords=["products", "skus", "catalog", "product range", "multiple products"],
        score_contribution=8,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Has product catalog",
    ),
    ICPRule(
        dimension="brand_size",
        evidence_keywords=["team", "employees", "staff", "headcount"],
        score_contribution=7,
        evidence_confidence=EvidenceConfidence.LOW,
        description="Has team (not solo)",
    ),
    ICPRule(
        dimension="mobile_commerce",
        evidence_keywords=["mobile", "app", "android", "ios"],
        score_contribution=10,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Has mobile commerce",
    ),
]

# ============================================================
# SAAS DEVELOPMENT RULES
# ============================================================

SAAS_DEVELOPMENT_RULES: list[ICPRule] = [
    ICPRule(
        dimension="saas_product",
        evidence_keywords=["saas", "software as a service", "subscription", "monthly plan",
                           "annual plan", "saas platform"],
        score_contribution=22,
        evidence_confidence=EvidenceConfidence.HIGH,
        description="Has SaaS product",
    ),
    ICPRule(
        dimension="technical_team",
        evidence_keywords=["developer", "engineer", "cto", "technical", "engineering",
                           "tech team", "dev team"],
        score_contribution=15,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Has technical team",
    ),
    ICPRule(
        dimension="product_stage",
        evidence_keywords=["mvp", "beta", "launch", "version", "product market fit",
                           "early stage", "pre-seed"],
        score_contribution=18,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Early-stage product",
    ),
    ICPRule(
        dimension="funding",
        evidence_keywords=["funded", "raised", "seed", "series a", "series b",
                           "investment", "venture"],
        score_contribution=12,
        evidence_confidence=EvidenceConfidence.HIGH,
        description="Has funding",
    ),
    ICPRule(
        dimension="team_size",
        evidence_keywords=["team", "employees", "headcount", "staff"],
        score_contribution=10,
        evidence_confidence=EvidenceConfidence.LOW,
        description="Has team",
    ),
    ICPRule(
        dimension="growth_trajectory",
        evidence_keywords=["scaling", "growing", "expanding", "fast growing", "rapid growth"],
        score_contribution=13,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Growing trajectory",
    ),
    ICPRule(
        dimension="product_market_fit",
        evidence_keywords=["customers", "users", "clients", "revenue", "arr", "mrr"],
        score_contribution=10,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Has product-market fit",
    ),
]

# ============================================================
# CUSTOM SOFTWARE RULES
# ============================================================

CUSTOM_SOFTWARE_RULES: list[ICPRule] = [
    ICPRule(
        dimension="custom_software_need",
        evidence_keywords=["custom software", "internal tool", "business application",
                           "bespoke software", "tailored solution"],
        score_contribution=22,
        evidence_confidence=EvidenceConfidence.HIGH,
        description="Needs custom software",
    ),
    ICPRule(
        dimension="legacy_systems",
        evidence_keywords=["legacy", "old system", "outdated", "manual process",
                           "spreadsheet", "paper-based"],
        score_contribution=18,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Has legacy systems",
    ),
    ICPRule(
        dimension="automation_need",
        evidence_keywords=["automation", "automate", "manual process", "inefficient",
                           "bottleneck", "time-consuming"],
        score_contribution=16,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Needs automation",
    ),
    ICPRule(
        dimension="enterprise_size",
        evidence_keywords=["enterprise", "large", "corporate", "organization", "company"],
        score_contribution=12,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Enterprise size",
    ),
    ICPRule(
        dimension="technology_operations",
        evidence_keywords=["technology", "digital", "data", "analytics", "reporting"],
        score_contribution=12,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="Technology operations",
    ),
    ICPRule(
        dimension="ai_requirement",
        evidence_keywords=["ai", "machine learning", "automation", "intelligent"],
        score_contribution=14,
        evidence_confidence=EvidenceConfidence.MEDIUM,
        description="AI/ML requirement",
    ),
    ICPRule(
        dimension="operational_complexity",
        evidence_keywords=["operations", "processes", "workflow", "supply chain",
                           "logistics", "inventory"],
        score_contribution=6,
        evidence_confidence=EvidenceConfidence.LOW,
        description="Complex operations",
    ),
]


def evaluate_icp(
    text: str,
    rules: list[ICPRule],
) -> ICPScore:
    """Evaluate a company against an ICP rule set.

    Returns ICPScore with score 0-100 and evidence.
    """
    text_lower = text.lower()
    matched_rules: list[tuple[ICPRule, list[str]]] = []

    for rule in rules:
        matched = [kw for kw in rule.evidence_keywords if kw in text_lower]
        if matched:
            matched_rules.append((rule, matched))

    total_score = sum(rule.score_contribution for rule, _ in matched_rules)
    total_score = min(total_score, 100.0)

    evidence = []
    signals_found = []
    for rule, matched_keywords in matched_rules:
        evidence.append(EvidenceRecord(
            claim=rule.description,
            value=f"Matched: {', '.join(matched_keywords[:3])}",
            source="icp_evaluation",
            source_url="",
            confidence=rule.evidence_confidence,
            observed_at=date.today(),
        ))
        signals_found.append(rule.dimension)

    missing = [
        rule.dimension for rule in rules
        if rule.dimension not in signals_found
    ]

    confidence = len(matched_rules) / len(rules) if rules else 0.0

    return ICPScore(
        score=total_score,
        confidence=round(confidence, 2),
        evidence=evidence,
        missing=missing,
        signals_found=signals_found,
    )


def score_all_icps(
    text: str,
    intent_level: IntentLevel = IntentLevel.NO_INTENT,
    intent_score: float = 0.0,
) -> dict[BusinessUnit, ICPScore]:
    """Score company against all three ICPs.

    Returns dict with BusinessUnit keys and ICPScore values.
    """
    return {
        BusinessUnit.COMAI: evaluate_icp(text, COMAI_RULES),
        BusinessUnit.SAAS_DEVELOPMENT: evaluate_icp(text, SAAS_DEVELOPMENT_RULES),
        BusinessUnit.CUSTOM_SOFTWARE: evaluate_icp(text, CUSTOM_SOFTWARE_RULES),
    }


def compute_opportunity_score(
    icp_fit: float,
    intent: float,
    buyability: float,
    intent_level: IntentLevel = IntentLevel.NO_INTENT,
) -> float:
    """Compute composite opportunity score.

    Formula: ICP * 0.3 + Intent * 0.4 + Buyability * 0.3

    Intent weighted 0.4 because CTO said: "explicit requirements
    should receive highest priority."

    Intent levels set floor:
    - ACTIVE_REQUIREMENT: floor 60
    - EVALUATION: floor 40
    - EARLY_INTENT: floor 20
    - COMPANY_OPPORTUNITY: floor 10
    - NO_INTENT: floor 0
    """
    raw = (icp_fit * 0.3) + (intent * 0.4) + (buyability * 0.3)

    floors = {
        IntentLevel.ACTIVE_REQUIREMENT: 60.0,
        IntentLevel.EVALUATION: 40.0,
        IntentLevel.EARLY_INTENT: 20.0,
        IntentLevel.COMPANY_OPPORTUNITY: 10.0,
        IntentLevel.NO_INTENT: 0.0,
    }

    floor = floors.get(intent_level, 0.0)
    return max(raw, floor)


def route_primary_business_unit(
    comai_score: ICPScore,
    saas_score: ICPScore,
    custom_score: ICPScore,
) -> tuple[BusinessUnit, list[BusinessUnit]]:
    """Route to primary and secondary business units.

    Primary = highest ICP score.
    Secondary = any ICP score above 40.
    """
    scores = {
        BusinessUnit.COMAI: comai_score.score,
        BusinessUnit.SAAS_DEVELOPMENT: saas_score.score,
        BusinessUnit.CUSTOM_SOFTWARE: custom_score.score,
    }

    sorted_bu = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = sorted_bu[0][0]

    secondary = [
        bu for bu, score in sorted_bu[1:]
        if score >= 40
    ]

    return primary, secondary
