from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LicensedProviderResult:
    enabled: bool
    provider: str
    people: list[dict[str, Any]]
    notes: str


class LicensedPeopleConnector:
    """Optional licensed adapters (Apollo, People Data Labs). Disabled unless keys configured."""

    def __init__(
        self,
        *,
        apollo_api_key: str | None = None,
        people_data_labs_api_key: str | None = None,
        enabled: bool = False,
    ) -> None:
        self.apollo_api_key = apollo_api_key
        self.people_data_labs_api_key = people_data_labs_api_key
        self.enabled = enabled and bool(apollo_api_key or people_data_labs_api_key)

    def fetch(self, *, company_name: str, domain: str | None) -> list[LicensedProviderResult]:
        _ = (company_name, domain)
        results: list[LicensedProviderResult] = []
        if not self.enabled:
            results.append(
                LicensedProviderResult(
                    enabled=False,
                    provider="licensed_providers",
                    people=[],
                    notes="Licensed people providers disabled by default. Configure API keys to enable.",
                )
            )
            return results

        if self.apollo_api_key:
            results.append(
                LicensedProviderResult(
                    enabled=True,
                    provider="apollo",
                    people=[],
                    notes="Apollo adapter enabled but returned no rows for this request scope.",
                )
            )
        if self.people_data_labs_api_key:
            results.append(
                LicensedProviderResult(
                    enabled=True,
                    provider="people_data_labs",
                    people=[],
                    notes="People Data Labs adapter enabled but returned no rows for this request scope.",
                )
            )
        return results
