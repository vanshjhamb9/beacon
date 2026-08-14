import hashlib
import html
import re
import unicodedata

from quality_engine.models.types import NormalizedQualityEvent, QualityEvent, QualityStage, StageResult

TAG_PATTERN = re.compile(r"<[^>]+>")
MARKDOWN_LINK_PATTERN = re.compile(r"\[([^\]]+)]\([^)]+\)")
WHITESPACE_PATTERN = re.compile(r"\s+")


class EventNormalizer:
    def normalize(self, event: QualityEvent) -> tuple[NormalizedQualityEvent, StageResult]:
        title = self._clean_text(event.title)
        content = self._clean_text(event.content)
        fingerprint_source = f"{event.source}|{event.url}|{title}|{content}".lower()
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        fingerprint = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()

        normalized = NormalizedQualityEvent(
            id=event.id,
            source=event.source.strip().lower(),
            url=event.url.strip(),
            title=title,
            content=content,
            published_at=event.published_at,
            collected_at=event.collected_at,
            metadata=event.metadata,
            event_hash=event.event_hash,
            normalized_language=self._language(event),
            content_hash=content_hash,
            fingerprint=fingerprint,
        )

        return normalized, StageResult(
            stage=QualityStage.NORMALIZATION,
            score=100.0,
            passed=True,
            details={
                "content_hash": content_hash,
                "fingerprint": fingerprint,
                "language": normalized.normalized_language,
            },
        )

    def _clean_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value)
        normalized = html.unescape(normalized)
        normalized = TAG_PATTERN.sub(" ", normalized)
        normalized = MARKDOWN_LINK_PATTERN.sub(r"\1", normalized)
        normalized = normalized.replace("\u200b", "")
        return WHITESPACE_PATTERN.sub(" ", normalized).strip()

    def _language(self, event: QualityEvent) -> str:
        language = event.metadata.get("language") or event.metadata.get("lang") or "en"
        return str(language).strip().lower()[:16] or "en"
