from __future__ import annotations

from data_verification.models.types import FieldObservation

_SOURCE_TRUST: dict[str, float] = {
    "user_provided": 95.0,
    "company_website": 88.0,
    "beacon_intelligence": 82.0,
    "beacon_context": 80.0,
    "beacon_revenue": 78.0,
    "beacon_opportunity": 76.0,
    "dns_mx": 84.0,
    "builtwith": 86.0,
    "wappalyzer": 86.0,
    "crunchbase": 85.0,
    "linkedin": 72.0,
    "github": 70.0,
    "twitter": 60.0,
    "product_hunt": 68.0,
    "g2": 70.0,
    "capterra": 70.0,
    "public_js": 74.0,
    "ssl_certificate": 80.0,
}


class TrustEngine:
    def score_source(self, source: str) -> float:
        return _SOURCE_TRUST.get(source.lower(), 55.0)

    def score_field(
        self,
        *,
        source: str,
        confidence: float,
        confirmed_by: list[str],
        conflicting_sources: list[str],
    ) -> float:
        base = self.score_source(source)
        confirmation_bonus = min(15.0, len(confirmed_by) * 7.5)
        conflict_penalty = min(30.0, len(conflicting_sources) * 15.0)
        confidence_factor = confidence * 0.25
        score = base * 0.55 + confidence_factor + confirmation_bonus - conflict_penalty
        return round(max(0.0, min(100.0, score)), 2)

    def score_profile(self, observations: list[FieldObservation]) -> float:
        if not observations:
            return 0.0
        scores = [self.score_source(item.source) * 0.7 + item.confidence * 0.3 for item in observations]
        return round(sum(scores) / len(scores), 2)
