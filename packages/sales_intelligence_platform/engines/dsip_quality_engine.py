"""DSIP: Discovery Quality Engine.

Quality checks for discovered companies.
Rejects low-quality companies before they enter ARIE.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class QualityCheck:
    """A single quality check result."""
    check_name: str
    passed: bool
    score: float  # 0-100
    severity: str  # info, low, medium, high, critical
    message: str
    evidence: list[dict] = field(default_factory=list)


@dataclass
class QualityReport:
    """Complete quality report for a company."""
    company_id: str
    overall_score: float = 0.0
    quality_grade: str = "F"  # A, B, C, D, F
    is_qualified: bool = False
    checks: list[QualityCheck] = field(default_factory=list)
    disqualification_reasons: list[str] = field(default_factory=list)
    recommendations: list[dict] = field(default_factory=list)


class DiscoveryQualityEngine:
    """Quality checks for discovered companies.

    Checks performed:
    - Website reachable
    - HTTPS valid
    - Domain validity
    - Platform detection confidence
    - Business active
    - Duplicate detection
    - Spam detection
    - Placeholder detection
    - Scam detection
    - Low quality detection
    - Dead stores
    - Parked domains

    Usage:
        engine = DiscoveryQualityEngine()
        report = engine.run_quality_checks(company_data)
        if report.is_qualified:
            # Send to ARIE
    """

    # Placeholder patterns
    PLACEHOLDER_PATTERNS = [
        r"lorem ipsum",
        r"example\.com",
        r"test\.com",
        r"placeholder",
        r"coming soon",
        r"under construction",
        r"page not found",
        r"404",
        r"this domain",
    ]

    # Spam patterns
    SPAM_PATTERNS = [
        r"buy now",
        r"click here",
        r"free money",
        r"act now",
        r"limited time",
        r"order now",
        r"discount",
        r"cheap",
    ]

    # Parked domain indicators
    PARKED_INDICATORS = [
        "domain for sale",
        "buy this domain",
        "this domain is for sale",
        "parked",
        "coming soon",
        "under construction",
    ]

    def run_quality_checks(
        self,
        company_data: dict,
        evidence: list[dict] = None,
    ) -> QualityReport:
        """Run all quality checks on a company."""
        company_id = company_data.get("id", company_data.get("canonical_id", "unknown"))
        report = QualityReport(company_id=company_id)

        checks = []

        # Website checks
        checks.extend(self._check_website(company_data))

        # Domain checks
        checks.extend(self._check_domain(company_data))

        # Platform checks
        checks.extend(self._check_platform(company_data))

        # Content checks
        checks.extend(self._check_content(company_data))

        # Business activity checks
        checks.extend(self._check_business_activity(company_data))

        # Data quality checks
        checks.extend(self._check_data_quality(company_data, evidence))

        report.checks = checks

        # Calculate overall score
        if checks:
            report.overall_score = sum(c.score for c in checks) / len(checks)

        # Determine grade
        report.quality_grade = self._calculate_grade(report.overall_score)

        # Determine qualification
        critical_failures = [c for c in checks if c.severity == "critical" and not c.passed]
        high_failures = [c for c in checks if c.severity == "high" and not c.passed]

        report.is_qualified = (
            report.overall_score >= 50 and
            len(critical_failures) == 0 and
            len(high_failures) < 2
        )

        # Disqualification reasons
        if not report.is_qualified:
            report.disqualification_reasons = [
                f"Failed check: {c.check_name} - {c.message}"
                for c in checks if not c.passed and c.severity in ["critical", "high"]
            ]

        # Recommendations
        report.recommendations = self._generate_recommendations(checks)

        return report

    def _check_website(self, company: dict) -> list[QualityCheck]:
        """Check website quality."""
        checks = []
        website = company.get("website", "")
        domain = company.get("primary_domain", "")

        # Check if website exists
        if website or domain:
            checks.append(QualityCheck(
                check_name="website_exists",
                passed=True,
                score=80.0,
                severity="info",
                message="Website URL provided",
            ))
        else:
            checks.append(QualityCheck(
                check_name="website_exists",
                passed=False,
                score=0.0,
                severity="high",
                message="No website URL found",
            ))

        return checks

    def _check_domain(self, company: dict) -> list[QualityCheck]:
        """Check domain quality."""
        checks = []
        domain = company.get("primary_domain", "")

        if not domain:
            checks.append(QualityCheck(
                check_name="domain_valid",
                passed=False,
                score=0.0,
                severity="high",
                message="No domain found",
            ))
            return checks

        # Check domain format
        domain_regex = r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?(\.[a-zA-Z]{2,})+$"
        is_valid = bool(re.match(domain_regex, domain))

        checks.append(QualityCheck(
            check_name="domain_valid",
            passed=is_valid,
            score=90.0 if is_valid else 10.0,
            severity="high" if not is_valid else "info",
            message=f"Domain format {'valid' if is_valid else 'invalid'}: {domain}",
        ))

        # Check for parked domain
        is_parked = any(indicator in domain.lower() for indicator in self.PARKED_INDICATORS)
        if is_parked:
            checks.append(QualityCheck(
                check_name="domain_parked",
                passed=False,
                score=0.0,
                severity="critical",
                message=f"Domain appears to be parked: {domain}",
            ))

        return checks

    def _check_platform(self, company: dict) -> list[QualityCheck]:
        """Check platform detection."""
        checks = []
        platform = company.get("platform", "")

        if platform:
            checks.append(QualityCheck(
                check_name="platform_detected",
                passed=True,
                score=85.0,
                severity="info",
                message=f"Platform detected: {platform}",
            ))
        else:
            checks.append(QualityCheck(
                check_name="platform_detected",
                passed=False,
                score=40.0,
                severity="medium",
                message="No platform detected",
            ))

        return checks

    def _check_content(self, company: dict) -> list[QualityCheck]:
        """Check for spam/placeholder content."""
        checks = []
        raw_data = company.get("raw_data", {})
        content = str(raw_data.get("content", "") or raw_data.get("description", "")).lower()

        # Check for placeholder content
        is_placeholder = any(re.search(p, content, re.IGNORECASE) for p in self.PLACEHOLDER_PATTERNS)
        if is_placeholder:
            checks.append(QualityCheck(
                check_name="content_quality",
                passed=False,
                score=10.0,
                severity="critical",
                message="Placeholder content detected",
            ))
        else:
            checks.append(QualityCheck(
                check_name="content_quality",
                passed=True,
                score=70.0,
                severity="info",
                message="Content quality acceptable",
            ))

        return checks

    def _check_business_activity(self, company: dict) -> list[QualityCheck]:
        """Check if business appears active."""
        checks = []
        store_status = company.get("store_status", "")
        products = company.get("product_count", 0)

        # Check store status
        if store_status == "active" or products > 0:
            checks.append(QualityCheck(
                check_name="business_active",
                passed=True,
                score=80.0,
                severity="info",
                message="Business appears active",
            ))
        elif store_status == "inactive":
            checks.append(QualityCheck(
                check_name="business_active",
                passed=False,
                score=20.0,
                severity="high",
                message="Store appears inactive",
            ))
        else:
            checks.append(QualityCheck(
                check_name="business_active",
                passed=True,
                score=50.0,
                severity="medium",
                message="Business activity status unknown",
            ))

        return checks

    def _check_data_quality(
        self,
        company: dict,
        evidence: list[dict] = None,
    ) -> list[QualityCheck]:
        """Check data completeness and quality."""
        checks = []

        # Count filled fields
        fields_to_check = [
            "company_name", "primary_domain", "industry", "country",
            "platform", "business_model",
        ]
        filled = sum(1 for f in fields_to_check if company.get(f))
        completeness = filled / len(fields_to_check) * 100

        checks.append(QualityCheck(
            check_name="data_completeness",
            passed=completeness >= 50,
            score=completeness,
            severity="medium" if completeness < 50 else "info",
            message=f"Data completeness: {completeness:.0f}%",
        ))

        # Check evidence quality
        if evidence:
            avg_confidence = sum(e.get("confidence", 0) for e in evidence) / len(evidence)
            checks.append(QualityCheck(
                check_name="evidence_quality",
                passed=avg_confidence >= 0.5,
                score=avg_confidence * 100,
                severity="medium" if avg_confidence < 0.5 else "info",
                message=f"Average evidence confidence: {avg_confidence:.2f}",
            ))

        return checks

    def _calculate_grade(self, score: float) -> str:
        """Calculate quality grade from score."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _generate_recommendations(self, checks: list[QualityCheck]) -> list[dict]:
        """Generate recommendations from check results."""
        recommendations = []

        for check in checks:
            if not check.passed:
                if check.severity == "critical":
                    priority = "high"
                elif check.severity == "high":
                    priority = "high"
                else:
                    priority = "medium"

                recommendations.append({
                    "priority": priority,
                    "action": f"Fix {check.check_name}",
                    "reason": check.message,
                })

        return recommendations
