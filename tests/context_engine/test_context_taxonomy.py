from tests.context_engine.test_context_pipeline import make_input

from context_engine.extractors.taxonomy import TaxonomyExtractor
from context_engine.rules.defaults import default_context_rules


def test_taxonomy_detects_business_pain_and_technology_terms() -> None:
    item = make_input()
    extractor = TaxonomyExtractor()

    pains = extractor.matching_pains(item)
    technologies = extractor.matching_technologies(item)

    assert "customer_support" in {term.key for term in pains}
    assert "zendesk" in {term.key for term in technologies}


def test_default_context_rules_are_versioned_and_explainable() -> None:
    rules = default_context_rules().all()

    assert all(rule.version >= 1 for rule in rules)
    assert all(rule.explanation for rule in rules)
    assert any(rule.key == "pain.support_pressure" for rule in rules)
