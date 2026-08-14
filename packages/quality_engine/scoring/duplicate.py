from difflib import SequenceMatcher

from quality_engine.models.types import NormalizedQualityEvent, QualityStage, StageResult


class DuplicateScorer:
    def score(
        self,
        event: NormalizedQualityEvent,
        *,
        known_hashes: set[str] | None = None,
        known_fingerprints: list[str] | None = None,
        processed_urls: set[str] | None = None,
    ) -> StageResult:
        known_hashes = known_hashes or set()
        known_fingerprints = known_fingerprints or []
        processed_urls = processed_urls or set()
        reasons: list[str] = []
        probability = 0.0

        if event.content_hash in known_hashes:
            probability = max(probability, 100.0)
            reasons.append("exact_duplicate")
        if event.url in processed_urls:
            probability = max(probability, 95.0)
            reasons.append("already_processed_url")

        if known_fingerprints:
            best = max(
                SequenceMatcher(None, event.fingerprint, fingerprint).ratio()
                for fingerprint in known_fingerprints
            )
            near_probability = round(best * 100.0, 4)
            if near_probability >= 88.0:
                reasons.append("near_duplicate")
            probability = max(probability, near_probability)

        if event.metadata.get("cross_source_duplicate") is True:
            probability = max(probability, 90.0)
            reasons.append("cross_source_duplicate")

        return StageResult(
            stage=QualityStage.DUPLICATE,
            score=round(probability, 4),
            passed=probability < 85.0,
            reason_codes=reasons,
            details={
                "content_hash": event.content_hash,
                "fingerprint": event.fingerprint,
                "semantic_similarity_model": "deterministic_fingerprint_v1",
            },
        )
