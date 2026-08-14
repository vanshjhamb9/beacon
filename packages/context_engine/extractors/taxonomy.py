from context_engine.models.types import BusinessContextInput
from context_engine.taxonomy.definitions import BUSINESS_PAIN_TERMS, TECHNOLOGY_TERMS, TaxonomyTerm


class TaxonomyExtractor:
    def matching_pains(self, item: BusinessContextInput) -> list[TaxonomyTerm]:
        return self._matches(item, list(BUSINESS_PAIN_TERMS))

    def matching_technologies(self, item: BusinessContextInput) -> list[TaxonomyTerm]:
        return self._matches(item, list(TECHNOLOGY_TERMS))

    def _matches(self, item: BusinessContextInput, terms: list[TaxonomyTerm]) -> list[TaxonomyTerm]:
        text = item.text
        matches: list[TaxonomyTerm] = []
        for term in terms:
            candidates = (term.key, term.label.lower(), *[alias.lower() for alias in term.aliases])
            if any(candidate in text for candidate in candidates):
                matches.append(term)
        return matches
