"""DSIP: Discovery Scoring Engine.

Creates composite Discovery Score for each company.
Only companies above threshold enter ARIE.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryScore:
    """Composite discovery score for a company."""
    company_id: str

    # Component Scores (0-100)
    source_quality: float = 0.0
    evidence_quality: float = 0.0
    website_quality: float = 0.0
    technology_detection: float = 0.0
    freshness: float = 0.0
    company_completeness: float = 0.0
    confidence: float = 0.0
    activity: float = 0.0
    canonical_confidence: float = 0.0

    # Composite
    discovery_score: float = 0.0
    qualified: bool = False
    classification: str = "UNSCORED"  # HOT, WARM, COLD, REJECTED, UNSCORED

    # Metadata
    threshold_used: float = 50.0
    scoring_version: str = "1.0"


class DiscoveryScoringEngine:
    """Creates composite Discovery Score for each company.

    Scoring Components (weighted):
    - Source Quality (15%): Reliability of discovery source
    - Evidence Quality (20%): Strength of evidence
    - Website Quality (10%): Website accessibility and quality
    - Technology Detection (10%): Tech stack identified
    - Freshness (10%): How recently data was updated
    - Company Completeness (15%): All fields filled
    - Confidence (10%): Overall confidence
    - Activity (5%): Business appears active
    - Canonical Confidence (5%): Identity resolution confidence

    Usage:
        engine = DiscoveryScoringEngine()
        score = engine.calculate_score(company_data, context)
        if score.qualified:
            # Send to ARIE
    """

    # Default weights
    WEIGHTS = {
        "source_quality": 0.15,
        "evidence_quality": 0.20,
        "website_quality": 0.10,
        "technology_detection": 0.10,
        "freshness": 0.10,
        "company_completeness": 0.15,
        "confidence": 0.10,
        "activity": 0.05,
        "canonical_confidence": 0.05,
    }

    # Classification thresholds
    THRESHOLDS = {
        "HOT": 80,
        "WARM": 65,
        "COLD": 50,
        "REJECTED": 0,
    }

    def __init__(self, qualification_threshold: float = 50.0):
        self.qualification_threshold = qualification_threshold

    def calculate_score(
        self,
        company_data: dict,
        context: dict = None,
    ) -> DiscoveryScore:
        """Calculate composite discovery score."""
        company_id = company_data.get("id", company_data.get("canonical_id", "unknown"))
        context = context or {}

        score = DiscoveryScore(company_id=company_id)

        # Calculate component scores
        score.source_quality = self._score_source_quality(company_data, context)
        score.evidence_quality = self._score_evidence_quality(company_data, context)
        score.website_quality = self._score_website_quality(company_data, context)
        score.technology_detection = self._score_technology(company_data, context)
        score.freshness = self._score_freshness(company_data, context)
        score.company_completeness = self._score_completeness(company_data)
        score.confidence = self._score_confidence(company_data)
        score.activity = self._score_activity(company_data, context)
        score.canonical_confidence = self._score_canonical(company_data, context)

        # Calculate composite score
        score.discovery_score = (
            score.source_quality * self.WEIGHTS["source_quality"] +
            score.evidence_quality * self.WEIGHTS["evidence_quality"] +
            score.website_quality * self.WEIGHTS["website_quality"] +
            score.technology_detection * self.WEIGHTS["technology_detection"] +
            score.freshness * self.WEIGHTS["freshness"] +
            score.company_completeness * self.WEIGHTS["company_completeness"] +
            score.confidence * self.WEIGHTS["confidence"] +
            score.activity * self.WEIGHTS["activity"] +
            score.canonical_confidence * self.WEIGHTS["canonical_confidence"]
        )

        # Determine qualification
        score.qualified = score.discovery_score >= self.qualification_threshold
        score.threshold_used = self.qualification_threshold

        # Classification
        score.classification = self._classify(score.discovery_score)

        return score

    def _score_source_quality(self, company: dict, context: dict) -> float:
        """Score based on source reliability."""
        source_reliability = context.get("source_reliability", 50.0)
        return min(100, max(0, source_reliability))

    def _score_evidence_quality(self, company: dict, context: dict) -> float:
        """Score based on evidence quality."""
        evidence = company.get("evidence", [])
        if not evidence:
            return 30.0  # Some base score for having data

        avg_confidence = sum(e.get("confidence", 0) for e in evidence) / len(evidence)
        source_count = len(set(e.get("source_id", "") for e in evidence))

        score = avg_confidence * 60 + min(40, source_count * 10)
        return min(100, max(0, score))

    def _score_website_quality(self, company: dict, context: dict) -> float:
        """Score based on website quality."""
        website = company.get("website", "")
        domain = company.get("primary_domain", "")

        if not website and not domain:
            return 20.0

        score = 50.0  # Base for having a website

        # HTTPS bonus
        if website and website.startswith("https"):
            score += 15

        # Domain quality
        if domain:
            tld = domain.split(".")[-1] if "." in domain else ""
            if tld in ["com", "in", "co.in", "net", "org"]:
                score += 15
            elif tld in ["io", "dev", "app"]:
                score += 10

        return min(100, max(0, score))

    def _score_technology(self, company: dict, context: dict) -> float:
        """Score based on technology detection."""
        technologies = company.get("technologies", [])
        platform = company.get("platform", "")

        if not technologies and not platform:
            return 20.0

        score = 30.0  # Base
        score += min(30, len(technologies) * 5)  # Tech count bonus
        if platform:
            score += 20  # Platform detected

        return min(100, max(0, score))

    def _score_freshness(self, company: dict, context: dict) -> float:
        """Score based on data freshness."""
        freshness = context.get("freshness_score", 50.0)
        return min(100, max(0, freshness))

    def _score_completeness(self, company: dict) -> float:
        """Score based on data completeness."""
        required_fields = [
            "company_name", "primary_domain", "industry", "country",
            "platform", "business_model",
        ]
        optional_fields = [
            "estimated_revenue", "estimated_employees", "estimated_traffic",
            "primary_email", "primary_phone",
        ]

        required_filled = sum(1 for f in required_fields if company.get(f))
        optional_filled = sum(1 for f in optional_fields if company.get(f))

        required_score = (required_filled / len(required_fields)) * 70
        optional_score = (optional_filled / len(optional_fields)) * 30

        return min(100, required_score + optional_score)

    def _score_confidence(self, company: dict) -> float:
        """Score based on overall confidence."""
        confidence = company.get("confidence", 0.5)
        return min(100, confidence * 100)

    def _score_activity(self, company: dict, context: dict) -> float:
        """Score based on business activity."""
        store_status = company.get("store_status", "")
        product_count = company.get("product_count", 0)
        traffic = company.get("estimated_traffic", 0)

        score = 40.0  # Base

        if store_status == "active":
            score += 25
        if product_count and product_count > 10:
            score += 15
        if traffic and traffic > 1000:
            score += 20

        return min(100, max(0, score))

    def _score_canonical(self, company: dict, context: dict) -> float:
        """Score based on canonical resolution confidence."""
        return context.get("canonical_confidence", 60.0)

    def _classify(self, score: float) -> str:
        """Classify based on score."""
        if score >= self.THRESHOLDS["HOT"]:
            return "HOT"
        elif score >= self.THRESHOLDS["WARM"]:
            return "WARM"
        elif score >= self.THRESHOLDS["COLD"]:
            return "COLD"
        else:
            return "REJECTED"

    def batch_score(
        self,
        companies: list[dict],
        context: dict = None,
    ) -> list[DiscoveryScore]:
        """Score multiple companies."""
        return [self.calculate_score(c, context) for c in companies]

    def get_scoring_stats(self, scores: list[DiscoveryScore]) -> dict:
        """Get statistics for a batch of scores."""
        if not scores:
            return {"total": 0}

        qualified = sum(1 for s in scores if s.qualified)
        hot = sum(1 for s in scores if s.classification == "HOT")
        warm = sum(1 for s in scores if s.classification == "WARM")
        cold = sum(1 for s in scores if s.classification == "COLD")
        rejected = sum(1 for s in scores if s.classification == "REJECTED")

        avg_score = sum(s.discovery_score for s in scores) / len(scores)

        return {
            "total": len(scores),
            "qualified": qualified,
            "qualification_rate": qualified / len(scores) * 100,
            "hot": hot,
            "warm": warm,
            "cold": cold,
            "rejected": rejected,
            "avg_score": avg_score,
        }
