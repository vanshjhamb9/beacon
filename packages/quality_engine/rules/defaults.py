from quality_engine.rules.definitions import QualityRuleDefinition, RuleCategory, RuleCatalog


def default_rule_catalog() -> RuleCatalog:
    return RuleCatalog(
        [
            QualityRuleDefinition(
                key="schema.required_fields",
                name="Required fields present",
                category=RuleCategory.SCHEMA,
                priority=10,
                threshold=100,
            ),
            QualityRuleDefinition(
                key="schema.valid_url",
                name="Valid absolute URL",
                category=RuleCategory.SCHEMA,
                priority=20,
                threshold=100,
            ),
            QualityRuleDefinition(
                key="schema.valid_timestamp",
                name="Valid timestamp",
                category=RuleCategory.SCHEMA,
                priority=30,
                threshold=100,
            ),
            QualityRuleDefinition(
                key="spam.keyword_patterns",
                name="Spam keyword and promotion patterns",
                category=RuleCategory.SPAM,
                priority=100,
                threshold=65,
                weight=0.35,
                parameters={
                    "terms": [
                        "buy now",
                        "limited time offer",
                        "affiliate",
                        "promo code",
                        "sponsored",
                        "guaranteed leads",
                        "click here",
                    ]
                },
            ),
            QualityRuleDefinition(
                key="spam.low_information",
                name="Low information density",
                category=RuleCategory.SPAM,
                priority=110,
                threshold=55,
                weight=0.2,
                parameters={"min_words": 12, "min_unique_ratio": 0.35},
            ),
            QualityRuleDefinition(
                key="spam.keyword_stuffing",
                name="Keyword stuffing",
                category=RuleCategory.SPAM,
                priority=120,
                threshold=55,
                weight=0.2,
                parameters={"max_repeated_word_ratio": 0.22},
            ),
            QualityRuleDefinition(
                key="duplicate.near_match",
                name="Near duplicate content fingerprint",
                category=RuleCategory.DUPLICATE,
                priority=200,
                threshold=85,
                weight=0.25,
            ),
            QualityRuleDefinition(
                key="source.community_default",
                name="Community source baseline trust",
                category=RuleCategory.TRUST,
                priority=300,
                threshold=50,
                parameters={
                    "reddit": 58,
                    "hacker_news": 72,
                    "product_hunt": 70,
                    "rss": 68,
                    "github_trending": 66,
                    "indie_hackers": 64,
                    "sec_edgar": 88,
                    "devto": 62,
                },
            ),
            QualityRuleDefinition(
                key="freshness.signal_age",
                name="Signal age freshness",
                category=RuleCategory.FRESHNESS,
                priority=400,
                threshold=40,
                # Phase 0 SLA: actionable leads must be ≤48h (2 days)
                parameters={"fresh_days": 1, "stale_days": 2, "expired_days": 2, "fresh_hours": 48},
            ),
            QualityRuleDefinition(
                key="completeness.minimum_text",
                name="Minimum text and metadata completeness",
                category=RuleCategory.COMPLETENESS,
                priority=500,
                threshold=60,
                parameters={"min_content_chars": 40},
            ),
            QualityRuleDefinition(
                key="entity.company_or_domain",
                name="Company or domain evidence",
                category=RuleCategory.ENTITY,
                priority=600,
                threshold=50,
            ),
            QualityRuleDefinition(
                key="score.acceptance",
                name="Quality acceptance threshold",
                category=RuleCategory.SCORING,
                priority=900,
                threshold=72,
                parameters={"review_threshold": 55, "reject_threshold": 45},
            ),
        ]
    )
