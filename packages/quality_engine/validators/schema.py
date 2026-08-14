from datetime import UTC
from urllib.parse import urlparse

from quality_engine.models.types import QualityEvent, QualityStage, StageResult


class SchemaValidator:
    def validate(self, event: QualityEvent) -> StageResult:
        reasons: list[str] = []

        if not event.source.strip():
            reasons.append("missing_source")
        if not event.url.strip():
            reasons.append("missing_url")
        if not event.title.strip():
            reasons.append("missing_title")
        if not event.content.strip():
            reasons.append("empty_content")

        parsed = urlparse(event.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            reasons.append("invalid_url")

        if event.published_at.tzinfo is None:
            reasons.append("timestamp_missing_timezone")
        elif event.published_at.astimezone(UTC).year < 1990:
            reasons.append("timestamp_out_of_range")

        try:
            event.content.encode("utf-8")
            event.title.encode("utf-8")
        except UnicodeEncodeError:
            reasons.append("encoding_error")

        score = max(0.0, 100.0 - (len(reasons) * 20.0))
        return StageResult(
            stage=QualityStage.SCHEMA,
            score=score,
            passed=not reasons,
            reason_codes=reasons,
            details={"checked_fields": ["source", "url", "title", "content", "published_at"]},
        )
