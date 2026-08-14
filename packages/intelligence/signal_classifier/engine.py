import re
from dataclasses import dataclass

from intelligence.types import ClassifiedSignalResult, Polarity, RawSignal, SignalCategory, Urgency


@dataclass(frozen=True)
class SignalRule:
    category: SignalCategory
    patterns: tuple[str, ...]
    subcategory: str | None
    business_function: str
    urgency: Urgency
    polarity: Polarity
    base_confidence: float


RULES: tuple[SignalRule, ...] = (
    SignalRule(SignalCategory.HIRING, ("hiring", "job opening", "we are recruiting", "open role"), "growth_hiring", "talent", Urgency.MEDIUM, Polarity.POSITIVE, 0.78),
    SignalRule(SignalCategory.FUNDING, ("raised", "funding", "series a", "series b", "seed round"), "capital_event", "finance", Urgency.HIGH, Polarity.POSITIVE, 0.86),
    SignalRule(SignalCategory.EXPANSION, ("opened", "new office", "expands to", "expansion", "launches in"), "geographic_expansion", "operations", Urgency.HIGH, Polarity.POSITIVE, 0.78),
    SignalRule(SignalCategory.CUSTOMER_SUPPORT, ("support team", "customer support", "help desk", "service desk"), "support_capacity", "support", Urgency.MEDIUM, Polarity.NEUTRAL, 0.72),
    SignalRule(SignalCategory.AI_ADOPTION, ("ai adoption", "artificial intelligence", "machine learning", "genai", "llm"), "ai_initiative", "technology", Urgency.HIGH, Polarity.POSITIVE, 0.76),
    SignalRule(SignalCategory.AUTOMATION, ("automation", "automate", "workflow", "rpa"), "process_automation", "operations", Urgency.MEDIUM, Polarity.POSITIVE, 0.73),
    SignalRule(SignalCategory.TECHNOLOGY_MIGRATION, ("migrating", "migration", "moving from", "replatform", "modernization"), "platform_change", "technology", Urgency.HIGH, Polarity.NEUTRAL, 0.8),
    SignalRule(SignalCategory.PARTNERSHIP, ("partners with", "partnership", "strategic alliance", "integration partner"), "partner_motion", "partnerships", Urgency.MEDIUM, Polarity.POSITIVE, 0.75),
    SignalRule(SignalCategory.PRODUCT_LAUNCH, ("launches", "launched", "released", "introduces", "new product"), "launch_event", "product", Urgency.HIGH, Polarity.POSITIVE, 0.82),
    SignalRule(SignalCategory.CUSTOMER_COMPLAINTS, ("complaint", "complaints", "terrible support", "outage", "broken", "not working"), "negative_feedback", "support", Urgency.CRITICAL, Polarity.NEGATIVE, 0.84),
    SignalRule(SignalCategory.HIRING_FREEZE, ("hiring freeze", "paused hiring", "headcount freeze"), "workforce_constraint", "talent", Urgency.HIGH, Polarity.NEGATIVE, 0.88),
    SignalRule(SignalCategory.LAYOFFS, ("layoffs", "laid off", "job cuts", "restructuring"), "workforce_reduction", "talent", Urgency.CRITICAL, Polarity.NEGATIVE, 0.9),
    SignalRule(SignalCategory.PRICING_CHANGES, ("pricing change", "raised prices", "price increase", "new pricing"), "pricing_event", "finance", Urgency.MEDIUM, Polarity.NEUTRAL, 0.77),
)


class RuleBasedSignalClassifier:
    def classify(self, signal: RawSignal) -> list[ClassifiedSignalResult]:
        text = signal.searchable_text
        results: list[ClassifiedSignalResult] = []

        for rule in RULES:
            matches = [pattern for pattern in rule.patterns if re.search(rf"\b{re.escape(pattern)}\b", text)]
            if not matches:
                continue

            confidence = min(0.98, rule.base_confidence + (0.03 * min(len(matches), 3)))
            results.append(
                ClassifiedSignalResult(
                    category=rule.category,
                    subcategory=rule.subcategory,
                    confidence=round(confidence, 4),
                    business_function=rule.business_function,
                    urgency=rule.urgency,
                    positive_or_negative=rule.polarity,
                    evidence={"matched_terms": matches, "classifier": "rule_based_v1"},
                )
            )

        if results:
            return sorted(results, key=lambda item: item.confidence, reverse=True)

        # Keep the funnel moving when entity resolution succeeded but no niche rule matched.
        tags = signal.metadata.get("signal_tags") if isinstance(signal.metadata, dict) else None
        return [
            ClassifiedSignalResult(
                category=SignalCategory.MARKET_MENTION,
                subcategory="general_market_activity",
                confidence=0.55,
                business_function="market_intelligence",
                urgency=Urgency.LOW,
                positive_or_negative=Polarity.NEUTRAL,
                evidence={
                    "matched_terms": tags if isinstance(tags, list) else [],
                    "classifier": "rule_based_v1_fallback",
                    "reason": "no_specialty_rule_matched",
                },
            )
        ]
