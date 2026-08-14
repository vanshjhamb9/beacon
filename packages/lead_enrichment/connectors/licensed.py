from __future__ import annotations

from collections.abc import Mapping

from lead_enrichment.models.types import (
    EnrichmentOpportunityInput,
    EnrichmentSourceType,
    LicensedProviderResult,
    TechnologyEntry,
)


class LicensedProviderConnector:
    """Optional licensed enrichment providers.

    Providers are only queried when an API key is configured. Without keys the
    connector returns disabled results so the pipeline stays lawful and offline-capable.
    """

    name = "licensed_providers"

    def __init__(self, *, api_keys: Mapping[str, str] | None = None) -> None:
        self.api_keys = {key.lower(): value for key, value in (api_keys or {}).items() if value}

    def collect(self, item: EnrichmentOpportunityInput) -> list[LicensedProviderResult]:
        results: list[LicensedProviderResult] = []
        domain = (item.domain or "").strip().lower()
        for provider, env_key, source in (
            ("builtwith", "builtwith", EnrichmentSourceType.BUILTWITH),
            ("wappalyzer", "wappalyzer", EnrichmentSourceType.WAPPALYZER),
            ("crunchbase", "crunchbase", EnrichmentSourceType.CRUNCHBASE),
        ):
            key = self.api_keys.get(env_key)
            if not key:
                results.append(
                    LicensedProviderResult(
                        provider=source,
                        enabled=False,
                        notes="API key not configured; skipped to remain lawful.",
                    )
                )
                continue
            # Licensed HTTP calls are intentionally not hard-coded against unpaid endpoints.
            # When keys are present, operators wire a licensed client; here we emit an
            # attribution marker so source tracking remains complete.
            results.append(
                LicensedProviderResult(
                    provider=source,
                    enabled=True,
                    technologies=(
                        [
                            TechnologyEntry(
                                name=f"{provider}_licensed_scan",
                                category="licensed_provider",
                                confidence=60.0,
                                source=source,
                                signal=f"licensed_ready:{domain or item.company_name}",
                            )
                        ]
                        if domain
                        else []
                    ),
                    notes="Licensed provider enabled; results require operator-configured client transport.",
                )
            )
        return results
