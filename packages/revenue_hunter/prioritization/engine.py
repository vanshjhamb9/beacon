from __future__ import annotations

from revenue_hunter.models.types import PriorityGrade, ScoreComponent


class PrioritizationEngine:
    """Rank A+ / A / B / C / D — only A+ and A enter campaigns by default."""

    def __init__(
        self,
        *,
        a_plus: float = 85.0,
        a_grade: float = 70.0,
        b_grade: float = 55.0,
        c_grade: float = 40.0,
    ) -> None:
        self.a_plus = a_plus
        self.a_grade = a_grade
        self.b_grade = b_grade
        self.c_grade = c_grade

    def grade(self, score: float) -> PriorityGrade:
        if score >= self.a_plus:
            return PriorityGrade.A_PLUS
        if score >= self.a_grade:
            return PriorityGrade.A
        if score >= self.b_grade:
            return PriorityGrade.B
        if score >= self.c_grade:
            return PriorityGrade.C
        return PriorityGrade.D

    def proceed_to_campaign(self, grade: PriorityGrade) -> bool:
        return grade in {PriorityGrade.A_PLUS, PriorityGrade.A}

    def score(
        self,
        *,
        filter_passed: bool,
        service_confidence: float,
        pain_confidence: float,
        website_opportunity_score: float,
        why_probability: float,
        opportunity_score: float,
        verification_score: float,
        has_decision_maker: bool,
    ) -> tuple[float, list[ScoreComponent], PriorityGrade]:
        weights = {
            "filter": 0.15,
            "service": 0.20,
            "pain": 0.15,
            "website": 0.10,
            "why_now": 0.20,
            "opportunity": 0.10,
            "access": 0.10,
        }
        filter_score = 100.0 if filter_passed else 20.0
        access = 75.0 if has_decision_maker else 35.0
        access += min(25.0, verification_score * 0.25)
        access = min(100.0, access)

        components = [
            ScoreComponent(
                name="filter",
                value=round(filter_score, 4),
                weight=weights["filter"],
                explanation="Target market / ICP filter gate",
                evidence=[f"passed:{filter_passed}"],
            ),
            ScoreComponent(
                name="service",
                value=round(service_confidence, 4),
                weight=weights["service"],
                explanation="Service match confidence",
                evidence=[f"confidence:{service_confidence}"],
            ),
            ScoreComponent(
                name="pain",
                value=round(pain_confidence, 4),
                weight=weights["pain"],
                explanation="Pain point strength",
                evidence=[f"pain_confidence:{pain_confidence}"],
            ),
            ScoreComponent(
                name="website",
                value=round(website_opportunity_score, 4),
                weight=weights["website"],
                explanation="Website improvement opportunity density",
                evidence=[f"website_opportunity:{website_opportunity_score}"],
            ),
            ScoreComponent(
                name="why_now",
                value=round(why_probability, 4),
                weight=weights["why_now"],
                explanation="Why-now buying probability",
                evidence=[f"probability:{why_probability}"],
            ),
            ScoreComponent(
                name="opportunity",
                value=round(min(100.0, opportunity_score), 4),
                weight=weights["opportunity"],
                explanation="Upstream opportunity score",
                evidence=[f"opportunity_score:{opportunity_score}"],
            ),
            ScoreComponent(
                name="access",
                value=round(access, 4),
                weight=weights["access"],
                explanation="Decision-maker / verification accessibility",
                evidence=[f"has_decision_maker:{has_decision_maker}", f"verification:{verification_score}"],
            ),
        ]
        total = sum(c.value * c.weight for c in components)
        # Hard floor when filter fails — never campaign-eligible
        if not filter_passed:
            total = min(total, 39.0)
        total = round(min(100.0, max(0.0, total)), 4)
        grade = self.grade(total)
        return total, components, grade
