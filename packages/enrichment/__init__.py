"""Enrichment pipeline for Intent-First Opportunity Discovery."""

from packages.enrichment.opportunity_enrichment import OpportunityEnricher, EnrichedOpportunity
from packages.enrichment.contact_enrichment import ContactEnricher, ContactInfo
from packages.enrichment.cross_source_validation import CrossSourceValidator, ValidationResult

__all__ = [
    "OpportunityEnricher",
    "EnrichedOpportunity",
    "ContactEnricher",
    "ContactInfo",
    "CrossSourceValidator",
    "ValidationResult",
]
