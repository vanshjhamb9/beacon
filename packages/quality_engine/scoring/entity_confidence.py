import re
from urllib.parse import urlparse

from quality_engine.models.types import NormalizedQualityEvent, QualityStage, StageResult

TECHNOLOGY_TERMS = {"aws", "azure", "gcp", "salesforce", "hubspot", "zendesk", "snowflake", "postgres"}
INDUSTRY_TERMS = {"retail", "fintech", "healthcare", "manufacturing", "saas", "logistics"}
LOCATION_PATTERN = re.compile(r"\b(uk|us|usa|europe|india|canada|germany|france|london|new york)\b", re.I)
PERSON_PATTERN = re.compile(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b")


class EntityConfidenceScorer:
    def score(self, event: NormalizedQualityEvent) -> StageResult:
        text = event.text
        lowered = text.lower()
        domain_present = bool(urlparse(event.url).netloc)
        company_present = bool(event.metadata.get("company") or event.metadata.get("company_name")) or domain_present
        person_present = bool(PERSON_PATTERN.search(text))
        technology_present = any(term in lowered for term in TECHNOLOGY_TERMS)
        industry_present = any(term in lowered for term in INDUSTRY_TERMS)
        location_present = bool(LOCATION_PATTERN.search(text))

        checks = {
            "company": company_present,
            "person": person_present,
            "technology": technology_present,
            "industry": industry_present,
            "location": location_present,
        }
        score = 30.0
        score += 30.0 if company_present else 0.0
        score += 12.0 if domain_present else 0.0
        score += 10.0 if technology_present else 0.0
        score += 8.0 if person_present else 0.0
        score += 5.0 if industry_present else 0.0
        score += 5.0 if location_present else 0.0
        score = min(100.0, score)
        return StageResult(
            stage=QualityStage.ENTITY_CONFIDENCE,
            score=round(score, 4),
            passed=score >= 50.0,
            reason_codes=[f"missing_{key}" for key, present in checks.items() if not present],
            details=checks,
        )
