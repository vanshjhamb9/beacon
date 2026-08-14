from collections import Counter
from difflib import SequenceMatcher

from quality_engine.models.types import NormalizedQualityEvent, QualityStage, StageResult
from quality_engine.rules.definitions import RuleCatalog, RuleCategory


class SpamScorer:
    def score(
        self,
        event: NormalizedQualityEvent,
        rules: RuleCatalog,
        *,
        recent_fingerprints: list[str] | None = None,
    ) -> StageResult:
        reasons: list[str] = []
        details: dict[str, object] = {}
        text = event.text.lower()
        words = [word for word in text.split() if word]
        spam_probability = 0.0

        keyword_rule = rules.by_key("spam.keyword_patterns")
        terms = list((keyword_rule.parameters if keyword_rule else {}).get("terms", []))
        matched_terms = [term for term in terms if str(term).lower() in text]
        if matched_terms:
            spam_probability += min(35.0, 10.0 * len(matched_terms))
            reasons.append("spam_keyword_match")
        details["matched_spam_terms"] = matched_terms

        low_info_rule = rules.by_key("spam.low_information")
        min_words = int((low_info_rule.parameters if low_info_rule else {}).get("min_words", 12))
        min_unique_ratio = float(
            (low_info_rule.parameters if low_info_rule else {}).get("min_unique_ratio", 0.35)
        )
        unique_ratio = len(set(words)) / max(1, len(words))
        if len(words) < min_words or unique_ratio < min_unique_ratio:
            spam_probability += 22.0
            reasons.append("low_information_content")
        details["word_count"] = len(words)
        details["unique_word_ratio"] = round(unique_ratio, 4)

        repeated_ratio = self._repeated_word_ratio(words)
        stuffing_rule = rules.by_key("spam.keyword_stuffing")
        max_repeated_ratio = float(
            (stuffing_rule.parameters if stuffing_rule else {}).get("max_repeated_word_ratio", 0.22)
        )
        if repeated_ratio > max_repeated_ratio:
            spam_probability += 20.0
            reasons.append("keyword_stuffing")
        details["repeated_word_ratio"] = repeated_ratio

        near_duplicate_probability = self._near_duplicate_probability(
            event.fingerprint,
            recent_fingerprints or [],
        )
        if near_duplicate_probability >= 70.0:
            spam_probability += 18.0
            reasons.append("near_duplicate_promotion")
        details["near_duplicate_probability"] = near_duplicate_probability

        if self._looks_bot_generated(text):
            spam_probability += 15.0
            reasons.append("bot_generated_pattern")

        spam_probability = min(100.0, spam_probability)
        return StageResult(
            stage=QualityStage.SPAM,
            score=round(spam_probability, 4),
            passed=spam_probability < 65.0,
            reason_codes=reasons,
            details=details,
        )

    def _repeated_word_ratio(self, words: list[str]) -> float:
        if not words:
            return 1.0
        counts = Counter(words)
        most_common = counts.most_common(1)[0][1]
        return round(most_common / len(words), 4)

    def _near_duplicate_probability(self, fingerprint: str, recent_fingerprints: list[str]) -> float:
        if fingerprint in recent_fingerprints:
            return 100.0
        if not recent_fingerprints:
            return 0.0
        best = max(SequenceMatcher(None, fingerprint, candidate).ratio() for candidate in recent_fingerprints)
        return round(best * 100.0, 4)

    def _looks_bot_generated(self, text: str) -> bool:
        generic_phrases = [
            "as an ai language model",
            "this article explores",
            "in today's fast-paced world",
            "unlock the power of",
        ]
        return any(phrase in text for phrase in generic_phrases)
