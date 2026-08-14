"""DQE v2 Quality Grade Engine — maps scores to grades and decisions."""

from __future__ import annotations

from discovery_quality_engine.v2_schemas import QualityGrade, QualityScore, grade_from_score


class QualityGradeEngine:
    """Maps quality scores to grades and determines decisions."""

    def __init__(
        self,
        *,
        a_plus_threshold: int = 95,
        a_threshold: int = 90,
        b_threshold: int = 85,
        c_threshold: int = 75,
    ) -> None:
        self._a_plus_threshold = a_plus_threshold
        self._a_threshold = a_threshold
        self._b_threshold = b_threshold
        self._c_threshold = c_threshold

    @property
    def thresholds(self) -> dict[str, int]:
        return {
            "a_plus": self._a_plus_threshold,
            "a": self._a_threshold,
            "b": self._b_threshold,
            "c": self._c_threshold,
        }

    def evaluate(self, score: QualityScore) -> QualityGrade:
        """Map a QualityScore to a QualityGrade."""
        return grade_from_score(score.total_score)

    def grade_to_decision(self, grade: QualityGrade) -> str:
        """Map a grade to a pipeline decision."""
        if grade in (QualityGrade.A_PLUS, QualityGrade.A, QualityGrade.B):
            return "ACCEPT"
        elif grade == QualityGrade.C:
            return "HOLD"
        else:
            return "REJECT"

    def get_decision(self, score: QualityScore) -> tuple[QualityGrade, str]:
        """Get both grade and decision for a score."""
        grade = self.evaluate(score)
        decision = self.grade_to_decision(grade)
        return grade, decision

    def is_acceptable(self, grade: QualityGrade) -> bool:
        """Check if a grade qualifies for ACCEPT."""
        return grade in (QualityGrade.A_PLUS, QualityGrade.A, QualityGrade.B)

    def is_hold(self, grade: QualityGrade) -> bool:
        """Check if a grade qualifies for HOLD."""
        return grade == QualityGrade.C

    def is_reject(self, grade: QualityGrade) -> bool:
        """Check if a grade qualifies for REJECT."""
        return grade == QualityGrade.REJECT
