from __future__ import annotations

from sales_intelligence.models.types import (
    BudgetBand,
    BuyingIntentResult,
    BuyingStage,
    SalesIntelligenceInput,
    UrgencyLevel,
)


class BuyingIntentEngine:
    def analyze(self, item: SalesIntelligenceInput) -> BuyingIntentResult:
        score = 25.0 + min(35.0, item.opportunity_score * 0.35) + min(20.0, item.probability * 0.2)
        evidence: list[str] = [f"opportunity_score:{item.opportunity_score}", f"probability:{item.probability}"]

        if item.funding_days_ago is not None and item.funding_days_ago <= 90:
            score += 12.0
            evidence.append(f"funding_days_ago:{item.funding_days_ago}")
        if item.hiring_count >= 3:
            score += 8.0
            evidence.append(f"hiring_count:{item.hiring_count}")
        if item.pains:
            score += min(10.0, len(item.pains) * 2.5)
            evidence.extend([f"pain:{p}" for p in item.pains[:4]])
        if item.signals:
            score += min(8.0, len(item.signals) * 1.5)
            evidence.extend([f"signal:{s}" for s in item.signals[:4]])
        if item.replies:
            score += min(10.0, len(item.replies) * 3.0)
            evidence.append(f"replies:{len(item.replies)}")
        if item.meetings:
            score += 8.0
            evidence.append(f"meetings:{len(item.meetings)}")
        if item.priority_grade in {"A+", "A"}:
            score += 6.0
            evidence.append(f"grade:{item.priority_grade}")

        score = round(min(100.0, max(0.0, score)), 4)
        stage = self._stage(score, item)
        urgency = self._urgency(item, score)
        budget = self._budget(item)
        window = 14 if urgency in {UrgencyLevel.HIGH, UrgencyLevel.CRITICAL} else (30 if score >= 60 else 60)
        complexity = "high" if (item.employee_count or 0) >= 250 or len(item.decision_makers) >= 3 else (
            "medium" if (item.employee_count or 0) >= 50 else "low"
        )
        confidence = round(min(95.0, 40.0 + score * 0.45 + (5.0 if item.decision_makers else 0.0)), 4)
        return BuyingIntentResult(
            buying_intent_score=score,
            buying_stage=stage,
            urgency=urgency,
            budget_probability=budget,
            decision_window_days=window,
            decision_complexity=complexity,
            buying_confidence=confidence,
            evidence_chain=evidence[:40],
        )

    def _stage(self, score: float, item: SalesIntelligenceInput) -> BuyingStage:
        if item.proposals or any("proposal" in str(o).lower() for o in item.outcomes):
            return BuyingStage.NEGOTIATION
        if item.meetings:
            return BuyingStage.VENDOR_EVALUATION
        if item.replies:
            return BuyingStage.SOLUTION_AWARE
        if score >= 70:
            return BuyingStage.SOLUTION_AWARE
        if score >= 45:
            return BuyingStage.PROBLEM_AWARE
        return BuyingStage.UNAWARE

    def _urgency(self, item: SalesIntelligenceInput, score: float) -> UrgencyLevel:
        if item.funding_days_ago is not None and item.funding_days_ago <= 30 and score >= 70:
            return UrgencyLevel.CRITICAL
        if (item.funding_days_ago is not None and item.funding_days_ago <= 90) or item.hiring_count >= 5:
            return UrgencyLevel.HIGH
        if score >= 55:
            return UrgencyLevel.MEDIUM
        return UrgencyLevel.LOW

    def _budget(self, item: SalesIntelligenceInput) -> BudgetBand:
        text = (item.expected_budget or item.revenue_band or "").lower()
        if "enterprise" in text or "100k" in text or "250k" in text:
            return BudgetBand.ENTERPRISE
        if "high" in text or "mid" in text or "60k" in text or "90k" in text:
            return BudgetBand.HIGH
        if "medium" in text or "smb" in text or "25k" in text or "45k" in text:
            return BudgetBand.MEDIUM
        count = item.employee_count or 0
        if count >= 500:
            return BudgetBand.ENTERPRISE
        if count >= 100:
            return BudgetBand.HIGH
        if count >= 25:
            return BudgetBand.MEDIUM
        return BudgetBand.LOW
