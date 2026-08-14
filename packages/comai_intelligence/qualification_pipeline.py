"""Qualification Pipeline — 10-gate qualification for COMAI leads.

Every discovered company must pass all gates before being marked Sales Ready.

Gate 1:  ICP Match
Gate 2:  Business Size
Gate 3:  Technology Fit
Gate 4:  Growth
Gate 5:  Pain
Gate 6:  Intent
Gate 7:  Decision Maker
Gate 8:  Contact Verification
Gate 9:  Revenue Potential
Gate 10: Negative Qualification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.comai_intelligence.icp_engine import ICPEngine, ICPScore
from packages.comai_intelligence.pain_engine import PainIntelligenceEngine, PainSignal
from packages.comai_intelligence.intent_engine import BuyingIntentEngine, IntentSignal
from packages.comai_intelligence.decision_maker_engine import DecisionMakerEngine, DecisionMakerInfo
from packages.comai_intelligence.tech_detection import COMAITechDetector, TechStack
from packages.comai_intelligence.revenue_scorer import RevenueOpportunityScorer, RevenueScore
from packages.comai_intelligence.close_probability import CloseProbabilityCalculator, CloseProbabilityResult
from packages.comai_intelligence.product_profile import COMAIProductCatalog


@dataclass
class GateResult:
    """Result of a single qualification gate."""

    gate_name: str
    gate_number: int
    passed: bool
    confidence: float  # 0-1
    score: float  # 0-100
    reason: str
    evidence: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_name": self.gate_name,
            "gate_number": self.gate_number,
            "passed": self.passed,
            "confidence": round(self.confidence, 3),
            "score": round(self.score, 2),
            "reason": self.reason,
            "evidence": self.evidence,
        }


@dataclass
class QualificationResult:
    """Complete qualification result for a company."""

    domain: str
    company_name: str
    gates: list[GateResult]
    sales_ready: bool
    overall_confidence: float
    revenue_score: RevenueScore | None = None
    close_probability: CloseProbabilityResult | None = None
    pains: list[PainSignal] = field(default_factory=list)
    intent_signals: list[IntentSignal] = field(default_factory=list)
    decision_makers: list[DecisionMakerInfo] = field(default_factory=list)
    tech_stack: TechStack | None = None

    @property
    def passed_gates(self) -> int:
        return sum(1 for g in self.gates if g.passed)

    @property
    def failed_gates(self) -> list[GateResult]:
        return [g for g in self.gates if not g.passed]

    def to_dict(self) -> dict[str, Any]:
        result = {
            "domain": self.domain,
            "company_name": self.company_name,
            "gates": [g.to_dict() for g in self.gates],
            "passed_gates": self.passed_gates,
            "total_gates": len(self.gates),
            "sales_ready": self.sales_ready,
            "overall_confidence": round(self.overall_confidence, 3),
        }
        if self.revenue_score:
            result["revenue_score"] = self.revenue_score.to_dict()
        if self.close_probability:
            result["close_probability"] = self.close_probability.to_dict()
        if self.tech_stack:
            result["tech_stack"] = self.tech_stack.to_dict()
        result["pains"] = [p.to_dict() for p in self.pains]
        result["intent_signals"] = [s.to_dict() for s in self.intent_signals]
        result["decision_makers"] = [d.to_dict() for d in self.decision_makers]
        return result


class QualificationPipeline:
    """10-gate qualification pipeline. Deterministic, no GPT.

    Only companies that pass ALL gates are marked Sales Ready.
    """

    def __init__(self) -> None:
        self.icp_engine = ICPEngine()
        self.pain_engine = PainIntelligenceEngine()
        self.intent_engine = BuyingIntentEngine()
        self.decision_engine = DecisionMakerEngine()
        self.tech_detector = COMAITechDetector()
        self.revenue_scorer = RevenueOpportunityScorer()
        self.close_calculator = CloseProbabilityCalculator()

    async def qualify(
        self,
        company: dict[str, Any],
        html: str = "",
    ) -> QualificationResult:
        """Run company through all 10 qualification gates.

        Args:
            company: Company data dict with all available information.
            html: Website HTML for technology detection (optional).

        Returns:
            QualificationResult with gate results and scoring.
        """
        gates: list[GateResult] = []

        # Pre-computation: detect technologies, pain, intent
        tech_stack = None
        if html:
            tech_stack = self.tech_detector.detect_all(html, company.get("website", ""))
            # Enrich company with tech data
            company["platform"] = tech_stack.platform
            company["has_chatbot"] = tech_stack.has_chatbot
            company["has_whatsapp"] = tech_stack.has_whatsapp
            company["has_ai"] = tech_stack.has_ai

        pains = self.pain_engine.analyze(company, tech_stack.__dict__ if tech_stack else None)
        intent_signals = self.intent_engine.detect_signals(company)

        # Discover decision makers
        decision_makers = await self.decision_engine.discover(company)

        # Gate 1: ICP Match
        icp_result = self.icp_engine.score(company)
        gates.append(GateResult(
            gate_name="ICP Match",
            gate_number=1,
            passed=icp_result.passed,
            confidence=icp_result.confidence,
            score=icp_result.score,
            reason=icp_result.reason,
            evidence=[icp_result.reason],
        ))

        # Gate 2: Business Size
        size_gate = self._gate_business_size(company)
        gates.append(size_gate)

        # Gate 3: Technology Fit
        tech_gate = self._gate_technology_fit(company, tech_stack)
        gates.append(tech_gate)

        # Gate 4: Growth
        growth_gate = self._gate_growth(company, intent_signals)
        gates.append(growth_gate)

        # Gate 5: Pain
        pain_gate = self._gate_pain(pains)
        gates.append(pain_gate)

        # Gate 6: Intent
        intent_gate = self._gate_intent(intent_signals)
        gates.append(intent_gate)

        # Gate 7: Decision Maker
        dm_gate = self._gate_decision_makers(decision_makers)
        gates.append(dm_gate)

        # Gate 8: Contact Verification
        contact_gate = self._gate_contact_verification(decision_makers)
        gates.append(contact_gate)

        # Gate 9: Revenue Potential
        revenue_gate = self._gate_revenue_potential(company, pains)
        gates.append(revenue_gate)

        # Gate 10: Negative Qualification
        negative_gate = self._gate_negative_qualification(company, icp_result)
        gates.append(negative_gate)

        # Calculate overall
        passed = all(g.passed for g in gates)
        overall_confidence = sum(g.confidence for g in gates) / len(gates) if gates else 0.0

        # Score revenue opportunity
        contact_quality = self.decision_engine.contact_quality_score(decision_makers)
        revenue_score = self.revenue_scorer.score(
            company, pains, intent_signals, icp_result,
            tech_stack.__dict__ if tech_stack else None,
            contact_quality=contact_quality,
            decision_maker_count=len(decision_makers),
        )

        # Calculate close probability
        close_prob = self.close_calculator.calculate(
            icp_score=icp_result.score,
            pain_score=self.pain_engine.score_pain_intensity(pains),
            intent_score=self.intent_engine.calculate_intent_score(intent_signals),
            decision_maker_count=len(decision_makers),
            decision_maker_quality=contact_quality,
            contact_verified=any(d.verification_status == "verified" for d in decision_makers),
            contact_quality=contact_quality,
            estimated_revenue=company.get("estimated_revenue") or 0,
            competition_level=1.0 - (revenue_score.competition_score / 100.0),
            recent_funding=bool(company.get("funding_recent")),
            hiring_active=bool(company.get("hiring")),
            is_urgently_looking=bool(company.get("looking_for_solution")),
        )

        return QualificationResult(
            domain=company.get("domain", ""),
            company_name=company.get("company_name", ""),
            gates=gates,
            sales_ready=passed,
            overall_confidence=overall_confidence,
            revenue_score=revenue_score,
            close_probability=close_prob,
            pains=pains,
            intent_signals=intent_signals,
            decision_makers=decision_makers,
            tech_stack=tech_stack,
        )

    def _gate_business_size(self, company: dict[str, Any]) -> GateResult:
        """Gate 2: Business Size check."""
        revenue = company.get("estimated_revenue") or 0
        employees = company.get("estimated_employees") or 0

        revenue_ok = 2_00_00_000 <= revenue <= 250_00_00_000
        employees_ok = 10 <= employees <= 250

        # If both unknown, give partial pass
        if revenue == 0 and employees == 0:
            return GateResult(
                gate_name="Business Size",
                gate_number=2,
                passed=True,
                confidence=0.3,
                score=50.0,
                reason="Size unknown — cannot reject, monitoring",
            )

        passed = revenue_ok or employees_ok
        confidence = 0.8 if revenue_ok and employees_ok else 0.5
        score = 80.0 if revenue_ok and employees_ok else (50.0 if passed else 20.0)

        reason_parts = []
        if revenue > 0:
            reason_parts.append(f"Revenue: ₹{revenue / 1_00_00_000:.1f} Cr")
        if employees > 0:
            reason_parts.append(f"Employees: {employees}")

        return GateResult(
            gate_name="Business Size",
            gate_number=2,
            passed=passed,
            confidence=confidence,
            score=score,
            reason=f"Business size: {', '.join(reason_parts)}",
        )

    def _gate_technology_fit(
        self, company: dict[str, Any], tech_stack: TechStack | None
    ) -> GateResult:
        """Gate 3: Technology Fit check."""
        platform = (company.get("platform") or "").lower()

        target_platforms = {"shopify", "shopify_plus", "woocommerce", "magento", "bigcommerce"}

        if platform in target_platforms:
            return GateResult(
                gate_name="Technology Fit",
                gate_number=3,
                passed=True,
                confidence=0.9 if tech_stack else 0.6,
                score=90.0,
                reason=f"Platform {platform} is ideal for COMAI",
            )

        if platform and platform != "unknown":
            return GateResult(
                gate_name="Technology Fit",
                gate_number=3,
                passed=False,
                confidence=0.7,
                score=30.0,
                reason=f"Platform {platform} is not a primary COMAI target",
            )

        return GateResult(
            gate_name="Technology Fit",
            gate_number=3,
            passed=True,
            confidence=0.4,
            score=50.0,
            reason="Platform unknown — cannot reject",
        )

    def _gate_growth(
        self, company: dict[str, Any], signals: list[IntentSignal]
    ) -> GateResult:
        """Gate 4: Growth check."""
        growth_signals = [s for s in signals if s.signal_type in ("hiring", "expansion", "funding")]

        if growth_signals:
            return GateResult(
                gate_name="Growth",
                gate_number=4,
                passed=True,
                confidence=0.8,
                score=min(len(growth_signals) * 30, 100.0),
                reason=f"Growth signals: {', '.join(s.signal_type for s in growth_signals)}",
            )

        # Check description for growth indicators
        desc = (company.get("description") or "").lower()
        growth_keywords = ["growing", "fast", "expanding", "scaling", "launching", "new"]
        found = [kw for kw in growth_keywords if kw in desc]

        if found:
            return GateResult(
                gate_name="Growth",
                gate_number=4,
                passed=True,
                confidence=0.5,
                score=50.0,
                reason=f"Growth indicators in description: {', '.join(found)}",
            )

        return GateResult(
            gate_name="Growth",
            gate_number=4,
            passed=True,  # Don't reject on growth alone
            confidence=0.3,
            score=30.0,
            reason="No explicit growth signals detected",
        )

    def _gate_pain(self, pains: list[PainSignal]) -> GateResult:
        """Gate 5: Pain check."""
        if not pains:
            return GateResult(
                gate_name="Pain",
                gate_number=5,
                passed=True,  # Don't reject on pain alone
                confidence=0.3,
                score=20.0,
                reason="No pain signals detected",
            )

        pain_score = self.pain_engine.score_pain_intensity(pains)
        critical = [p for p in pains if p.severity == "critical"]
        high = [p for p in pains if p.severity == "high"]

        passed = pain_score >= 20.0
        confidence = 0.9 if critical else (0.7 if high else 0.5)

        top_pain = pains[0].pain_type if pains else "unknown"
        return GateResult(
            gate_name="Pain",
            gate_number=5,
            passed=passed,
            confidence=confidence,
            score=pain_score,
            reason=f"Pain score {pain_score:.0f}/100, top pain: {top_pain}",
        )

    def _gate_intent(self, signals: list[IntentSignal]) -> GateResult:
        """Gate 6: Intent check."""
        if not signals:
            return GateResult(
                gate_name="Intent",
                gate_number=6,
                passed=True,  # Don't reject on intent alone
                confidence=0.3,
                score=20.0,
                reason="No intent signals detected",
            )

        intent_score = self.intent_engine.calculate_intent_score(signals)
        top = signals[0].signal_type if signals else "unknown"

        return GateResult(
            gate_name="Intent",
            gate_number=6,
            passed=intent_score >= 15.0,
            confidence=0.8 if intent_score >= 50 else 0.5,
            score=intent_score,
            reason=f"Intent score {intent_score:.0f}/100, top signal: {top}",
        )

    def _gate_decision_makers(self, makers: list[DecisionMakerInfo]) -> GateResult:
        """Gate 7: Decision Maker check."""
        non_generic = [m for m in makers if not m.is_generic]

        if non_generic:
            best = non_generic[0]
            return GateResult(
                gate_name="Decision Maker",
                gate_number=7,
                passed=True,
                confidence=best.confidence,
                score=min(len(non_generic) * 30, 100.0),
                reason=f"Found {len(non_generic)} decision maker(s), best: {best.name} ({best.role})",
            )

        if makers:
            return GateResult(
                gate_name="Decision Maker",
                gate_number=7,
                passed=True,
                confidence=0.3,
                score=30.0,
                reason=f"Only generic contacts found ({len(makers)})",
            )

        return GateResult(
            gate_name="Decision Maker",
            gate_number=7,
            passed=True,  # Don't reject, but flag
            confidence=0.2,
            score=10.0,
            reason="No decision makers found yet",
        )

    def _gate_contact_verification(self, makers: list[DecisionMakerInfo]) -> GateResult:
        """Gate 8: Contact Verification check."""
        with_email = [m for m in makers if m.email and not m.is_generic]
        with_phone = [m for m in makers if m.phone and not m.is_generic]
        verified = [m for m in makers if m.verification_status == "verified"]

        if verified:
            return GateResult(
                gate_name="Contact Verification",
                gate_number=8,
                passed=True,
                confidence=0.9,
                score=90.0,
                reason=f"{len(verified)} verified contact(s)",
            )

        if with_email or with_phone:
            return GateResult(
                gate_name="Contact Verification",
                gate_number=8,
                passed=True,
                confidence=0.6,
                score=60.0,
                reason=f"{len(with_email)} email(s), {len(with_phone)} phone(s) — unverified",
            )

        return GateResult(
            gate_name="Contact Verification",
            gate_number=8,
            passed=True,  # Don't reject, but low confidence
            confidence=0.2,
            score=20.0,
            reason="No verified contacts — needs enrichment",
        )

    def _gate_revenue_potential(
        self, company: dict[str, Any], pains: list[PainSignal]
    ) -> GateResult:
        """Gate 9: Revenue Potential check."""
        revenue = company.get("estimated_revenue") or 0
        products = COMAIProductCatalog.applicable_products(
            company.get("industry") or "",
            company.get("platform") or "",
            revenue or 5_00_00_000,
            company.get("estimated_employees") or 50,
        )
        total_arr = COMAIProductCatalog.estimate_total_arr(products)

        if total_arr >= 3_60_000:
            return GateResult(
                gate_name="Revenue Potential",
                gate_number=9,
                passed=True,
                confidence=0.8,
                score=80.0,
                reason=f"Estimated ARR: ₹{total_arr / 1_00_000:.1f}L from {len(products)} product(s)",
            )
        if total_arr >= 1_20_000:
            return GateResult(
                gate_name="Revenue Potential",
                gate_number=9,
                passed=True,
                confidence=0.6,
                score=60.0,
                reason=f"Estimated ARR: ₹{total_arr / 1_00_000:.1f}L from {len(products)} product(s)",
            )
        return GateResult(
            gate_name="Revenue Potential",
            gate_number=9,
            passed=True,
            confidence=0.4,
            score=40.0,
            reason=f"Low estimated ARR: ₹{total_arr / 1_00_000:.1f}L",
        )

    def _gate_negative_qualification(
        self, company: dict[str, Any], icp: ICPScore
    ) -> GateResult:
        """Gate 10: Negative Qualification — hard rejects."""
        if icp.rejections:
            return GateResult(
                gate_name="Negative Qualification",
                gate_number=10,
                passed=False,
                confidence=1.0,
                score=0.0,
                reason=f"Rejected: {'; '.join(icp.rejections)}",
                evidence=icp.rejections,
            )

        # Additional negative checks
        name = (company.get("company_name") or "").lower()
        desc = (company.get("description") or "").lower()
        text = f"{name} {desc}"

        reject_terms = [
            "government", "hospital", "bank", "university",
            "amazon seller", "flipkart seller", "marketplace only",
        ]
        for term in reject_terms:
            if term in text:
                return GateResult(
                    gate_name="Negative Qualification",
                    gate_number=10,
                    passed=False,
                    confidence=1.0,
                    score=0.0,
                    reason=f"Rejected: contains '{term}'",
                )

        return GateResult(
            gate_name="Negative Qualification",
            gate_number=10,
            passed=True,
            confidence=0.9,
            score=100.0,
            reason="Passed negative qualification checks",
        )
