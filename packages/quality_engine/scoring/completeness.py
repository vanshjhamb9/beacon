from urllib.parse import urlparse

from quality_engine.models.types import NormalizedQualityEvent, QualityStage, StageResult
from quality_engine.rules.definitions import RuleCatalog


class CompletenessScorer:
    def score(self, event: NormalizedQualityEvent, rules: RuleCatalog) -> StageResult:
        rule = rules.by_key("completeness.minimum_text")
        min_content_chars = int((rule.parameters if rule else {}).get("min_content_chars", 40))
        checks = {
            "company_present": self._company_present(event),
            "url_present": bool(event.url),
            "domain_present": bool(urlparse(event.url).netloc),
            "timestamp_present": event.published_at is not None,
            "enough_text": len(event.content) >= min_content_chars,
            "metadata_quality": len(event.metadata) > 0,
        }
        score = sum(1 for passed in checks.values() if passed) / len(checks) * 100.0
        reasons = [f"missing_{key}" for key, passed in checks.items() if not passed]
        return StageResult(
            stage=QualityStage.COMPLETENESS,
            score=round(score, 4),
            passed=score >= 60.0,
            reason_codes=reasons,
            details=checks,
        )

    def _company_present(self, event: NormalizedQualityEvent) -> bool:
        metadata_company = event.metadata.get("company") or event.metadata.get("company_name")
        title_has_capitalized_token = any(token[:1].isupper() for token in event.title.split())
        return bool(metadata_company) or title_has_capitalized_token
