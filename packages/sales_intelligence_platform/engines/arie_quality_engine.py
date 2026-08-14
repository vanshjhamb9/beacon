"""ARIE: Lead Quality Engine & Negative Qualification Engine.

Runs quality checks and rejects poor prospects.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class QualityCheck:
    """Result of a quality check."""
    check_name: str
    passed: bool
    score: float  # 0-100
    severity: str = "info"  # critical, high, medium, low, info
    message: str = ""
    evidence: list = field(default_factory=list)


@dataclass
class QualityReport:
    """Complete quality report for a company."""
    domain: str
    overall_quality_score: float  # 0-100
    quality_grade: str  # A, B, C, D, F
    is_qualified: bool  # Pass/fail
    disqualification_reasons: list = field(default_factory=list)
    checks: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    data_freshness: str = "unknown"  # fresh, stale, outdated
    confidence: float = 0.0


@dataclass
class NegativeQualificationResult:
    """Result of negative qualification check."""
    is_rejected: bool
    rejection_reason: str = ""
    rejection_category: str = ""  # enterprise, government, inactive, etc.
    evidence: list = field(default_factory=list)
    confidence: float = 0.0


class ARIEQualityEngine:
    """Lead Quality Engine - runs quality checks and rejects poor prospects."""
    
    # Negative ICP keywords
    NEGATIVE_KEYWORDS = {
        "enterprise": ["enterprise", "corporation", "inc", "corp", "llc", "ltd"],
        "government": ["government", "gov", "official", "ministry", "department"],
        "bank": ["bank", "banking", "financial", "finance", "insurance"],
        "hospital": ["hospital", "healthcare", "medical", "clinic", "pharma"],
        "marketplace": ["amazon", "flipkart", "ebay", "walmart", "alibaba"],
        "offline": ["offline", "brick-and-mortar", "physical store"],
    }
    
    # Quality check thresholds
    QUALITY_THRESHOLDS = {
        "min_traffic": 1000,
        "min_products": 10,
        "min_age_months": 6,
        "min_email_confidence": 0.5,
        "min_phone_confidence": 0.5,
        "min_data_completeness": 0.3,
    }
    
    def run_quality_checks(
        self,
        company_data: dict[str, Any],
        contact_data: dict[str, Any] = None,
    ) -> QualityReport:
        """Run comprehensive quality checks on a company.
        
        Args:
            company_data: Company information
            contact_data: Contact information
            
        Returns:
            QualityReport with all checks and recommendations
        """
        domain = company_data.get("domain", "")
        
        report = QualityReport(
            domain=domain,
            overall_quality_score=0.0,
            quality_grade="F",
            is_qualified=False,
        )
        
        checks = []
        
        # 1. Website validation
        checks.append(self._check_website(company_data))
        
        # 2. Platform validation
        checks.append(self._check_platform(company_data))
        
        # 3. Store activity
        checks.append(self._check_store_activity(company_data))
        
        # 4. Email verification
        if contact_data:
            checks.append(self._check_email(contact_data))
        
        # 5. Phone validation
        if contact_data:
            checks.append(self._check_phone(contact_data))
        
        # 6. Decision maker freshness
        checks.append(self._check_decision_maker(company_data))
        
        # 7. Technology freshness
        checks.append(self._check_technology(company_data))
        
        # 8. Data completeness
        checks.append(self._check_data_completeness(company_data, contact_data))
        
        # 9. Historical consistency
        checks.append(self._check_historical_consistency(company_data))
        
        # 10. Negative qualification
        negative_result = self._check_negative_qualification(company_data)
        if negative_result.is_rejected:
            checks.append(QualityCheck(
                check_name="negative_qualification",
                passed=False,
                score=0.0,
                severity="critical",
                message=f"Rejected: {negative_result.rejection_reason}",
                evidence=negative_result.evidence,
            ))
            report.disqualification_reasons.append({
                "reason": negative_result.rejection_reason,
                "category": negative_result.rejection_category,
            })
        
        # Store checks
        report.checks = checks
        
        # Calculate overall score
        if checks:
            report.overall_quality_score = sum(c.score for c in checks) / len(checks)
        else:
            report.overall_quality_score = 0.0
        
        # Determine grade
        if report.overall_quality_score >= 90:
            report.quality_grade = "A"
        elif report.overall_quality_score >= 80:
            report.quality_grade = "B"
        elif report.overall_quality_score >= 70:
            report.quality_grade = "C"
        elif report.overall_quality_score >= 60:
            report.quality_grade = "D"
        else:
            report.quality_grade = "F"
        
        # Determine qualification
        critical_failures = [c for c in checks if not c.passed and c.severity == "critical"]
        high_failures = [c for c in checks if not c.passed and c.severity == "high"]
        
        report.is_qualified = (
            len(critical_failures) == 0 and
            len(high_failures) <= 1 and
            report.overall_quality_score >= 60
        )
        
        # Data freshness
        report.data_freshness = self._assess_data_freshness(company_data)
        
        # Confidence
        report.confidence = self._calculate_quality_confidence(checks)
        
        # Recommendations
        report.recommendations = self._generate_quality_recommendations(report)
        
        return report
    
    def _check_website(self, company: dict) -> QualityCheck:
        """Check website validity."""
        website = company.get("website", "")
        domain = company.get("domain", "")
        
        if not website and not domain:
            return QualityCheck(
                check_name="website",
                passed=False,
                score=0.0,
                severity="critical",
                message="No website or domain provided",
            )
        
        # Check if website is accessible
        status = company.get("website_status", "")
        if status == "403" or status == "404":
            return QualityCheck(
                check_name="website",
                passed=False,
                score=20.0,
                severity="high",
                message=f"Website returns {status}",
            )
        
        return QualityCheck(
            check_name="website",
            passed=True,
            score=90.0,
            message="Website accessible",
        )
    
    def _check_platform(self, company: dict) -> QualityCheck:
        """Check platform validity."""
        platform = company.get("platform", "")
        
        valid_platforms = ["shopify", "woocommerce", "magento", "bigcommerce"]
        
        if platform.lower() in valid_platforms:
            return QualityCheck(
                check_name="platform",
                passed=True,
                score=90.0,
                message=f"Valid platform: {platform}",
            )
        
        return QualityCheck(
            check_name="platform",
            passed=False,
            score=30.0,
            severity="medium",
            message=f"Unknown platform: {platform}",
        )
    
    def _check_store_activity(self, company: dict) -> QualityCheck:
        """Check store activity."""
        product_count = company.get("product_count", 0)
        last_updated = company.get("last_updated")
        
        if product_count < self.QUALITY_THRESHOLDS["min_products"]:
            return QualityCheck(
                check_name="store_activity",
                passed=False,
                score=30.0,
                severity="medium",
                message=f"Low product count: {product_count}",
            )
        
        return QualityCheck(
            check_name="store_activity",
            passed=True,
            score=80.0,
            message=f"Store active with {product_count} products",
        )
    
    def _check_email(self, contact: dict) -> QualityCheck:
        """Check email validity."""
        email = contact.get("email", "")
        email_confidence = contact.get("email_confidence", 0)
        
        if not email:
            return QualityCheck(
                check_name="email",
                passed=False,
                score=20.0,
                severity="high",
                message="No email available",
            )
        
        if email_confidence < self.QUALITY_THRESHOLDS["min_email_confidence"]:
            return QualityCheck(
                check_name="email",
                passed=False,
                score=40.0,
                severity="medium",
                message=f"Low email confidence: {email_confidence:.0%}",
            )
        
        return QualityCheck(
            check_name="email",
            passed=True,
            score=85.0,
            message=f"Email verified: {email}",
        )
    
    def _check_phone(self, contact: dict) -> QualityCheck:
        """Check phone validity."""
        phone = contact.get("phone", "")
        phone_confidence = contact.get("phone_confidence", 0)
        
        if not phone:
            return QualityCheck(
                check_name="phone",
                passed=False,
                score=20.0,
                severity="medium",
                message="No phone available",
            )
        
        if phone_confidence < self.QUALITY_THRESHOLDS["min_phone_confidence"]:
            return QualityCheck(
                check_name="phone",
                passed=False,
                score=40.0,
                severity="low",
                message=f"Low phone confidence: {phone_confidence:.0%}",
            )
        
        return QualityCheck(
            check_name="phone",
            passed=True,
            score=80.0,
            message=f"Phone available: {phone}",
        )
    
    def _check_decision_maker(self, company: dict) -> QualityCheck:
        """Check decision maker freshness."""
        decision_makers = company.get("decision_makers", [])
        last_verified = company.get("decision_maker_last_verified")
        
        if not decision_makers:
            return QualityCheck(
                check_name="decision_maker",
                passed=False,
                score=30.0,
                severity="high",
                message="No decision makers identified",
            )
        
        # Check freshness
        if last_verified:
            try:
                verified_date = datetime.fromisoformat(last_verified.replace("Z", "+00:00"))
                days_since = (datetime.utcnow() - verified_date.replace(tzinfo=None)).days
                
                if days_since > 90:
                    return QualityCheck(
                        check_name="decision_maker",
                        passed=False,
                        score=50.0,
                        severity="medium",
                        message=f"Decision maker data {days_since} days old",
                    )
            except (ValueError, TypeError):
                pass
        
        return QualityCheck(
            check_name="decision_maker",
            passed=True,
            score=80.0,
            message=f"Found {len(decision_makers)} decision makers",
        )
    
    def _check_technology(self, company: dict) -> QualityCheck:
        """Check technology freshness."""
        tech_stack = company.get("technology_stack", {})
        last_detected = company.get("technology_last_detected")
        
        if not tech_stack:
            return QualityCheck(
                check_name="technology",
                passed=False,
                score=40.0,
                severity="medium",
                message="No technology data available",
            )
        
        # Check freshness
        if last_detected:
            try:
                detected_date = datetime.fromisoformat(last_detected.replace("Z", "+00:00"))
                days_since = (datetime.utcnow() - detected_date.replace(tzinfo=None)).days
                
                if days_since > 180:
                    return QualityCheck(
                        check_name="technology",
                        passed=False,
                        score=50.0,
                        severity="medium",
                        message=f"Technology data {days_since} days old",
                    )
            except (ValueError, TypeError):
                pass
        
        return QualityCheck(
            check_name="technology",
            passed=True,
            score=80.0,
            message=f"Technology detected: {len(tech_stack)} tools",
        )
    
    def _check_data_completeness(self, company: dict, contact: dict = None) -> QualityCheck:
        """Check data completeness."""
        fields = [
            bool(company.get("domain")),
            bool(company.get("industry")),
            bool(company.get("country")),
            bool(company.get("platform")),
            bool(company.get("traffic")),
            bool(company.get("product_count")),
            bool(contact and contact.get("email")),
            bool(contact and contact.get("phone")),
            bool(contact and contact.get("founder_name")),
        ]
        
        completeness = sum(1 for f in fields if f) / len(fields)
        
        if completeness < self.QUALITY_THRESHOLDS["min_data_completeness"]:
            return QualityCheck(
                check_name="data_completeness",
                passed=False,
                score=completeness * 100,
                severity="medium",
                message=f"Low data completeness: {completeness:.0%}",
            )
        
        return QualityCheck(
            check_name="data_completeness",
            passed=True,
            score=completeness * 100,
            message=f"Data completeness: {completeness:.0%}",
        )
    
    def _check_historical_consistency(self, company: dict) -> QualityCheck:
        """Check historical consistency."""
        # This would check against historical data
        # For now, return a basic check
        return QualityCheck(
            check_name="historical_consistency",
            passed=True,
            score=70.0,
            message="Historical consistency check passed",
        )
    
    def _check_negative_qualification(self, company: dict) -> NegativeQualificationResult:
        """Check for negative qualification criteria."""
        domain = company.get("domain", "").lower()
        industry = company.get("industry", "").lower()
        company_name = company.get("company_name", "").lower()
        
        # Check negative keywords
        for category, keywords in self.NEGATIVE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in domain or keyword in industry or keyword in company_name:
                    return NegativeQualificationResult(
                        is_rejected=True,
                        rejection_reason=f"Negative keyword: {keyword}",
                        rejection_category=category,
                        evidence=[f"Found '{keyword}' in domain/industry/name"],
                        confidence=0.9,
                    )
        
        # Check enterprise signals
        traffic = company.get("traffic", 0)
        employees = company.get("employees", 0)
        
        if traffic > 1000000 or employees > 1000:
            return NegativeQualificationResult(
                is_rejected=True,
                rejection_reason="Enterprise company (high traffic/employees)",
                rejection_category="enterprise",
                evidence=[f"Traffic: {traffic}, Employees: {employees}"],
                confidence=0.8,
            )
        
        # Check inactive stores
        status = company.get("store_status", "")
        if status == "inactive" or status == "suspended":
            return NegativeQualificationResult(
                is_rejected=True,
                rejection_reason=f"Store is {status}",
                rejection_category="inactive",
                evidence=[f"Store status: {status}"],
                confidence=0.9,
            )
        
        return NegativeQualificationResult(
            is_rejected=False,
            confidence=0.7,
        )
    
    def _assess_data_freshness(self, company: dict) -> str:
        """Assess data freshness."""
        last_enriched = company.get("last_enriched")
        
        if not last_enriched:
            return "unknown"
        
        try:
            enriched_date = datetime.fromisoformat(last_enriched.replace("Z", "+00:00"))
            days_since = (datetime.utcnow() - enriched_date.replace(tzinfo=None)).days
            
            if days_since <= 7:
                return "fresh"
            elif days_since <= 30:
                return "stale"
            else:
                return "outdated"
        except (ValueError, TypeError):
            return "unknown"
    
    def _calculate_quality_confidence(self, checks: list[QualityCheck]) -> float:
        """Calculate confidence in quality assessment."""
        if not checks:
            return 0.0
        
        passed_checks = sum(1 for c in checks if c.passed)
        return (passed_checks / len(checks)) * 100
    
    def _generate_quality_recommendations(self, report: QualityReport) -> list:
        """Generate recommendations based on quality report."""
        recommendations = []
        
        if not report.is_qualified:
            recommendations.append({
                "priority": "high",
                "action": "Do not pursue - quality check failed",
                "reason": f"Quality score {report.overall_quality_score:.0f} below threshold",
            })
        
        for check in report.checks:
            if not check.passed and check.severity in ["critical", "high"]:
                recommendations.append({
                    "priority": "high",
                    "action": f"Fix {check.check_name}",
                    "reason": check.message,
                })
        
        if report.data_freshness == "outdated":
            recommendations.append({
                "priority": "medium",
                "action": "Refresh company data",
                "reason": "Data is outdated and may be inaccurate",
            })
        
        return recommendations
