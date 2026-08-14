"""Licensed directory provider contracts — interfaces only until credentials exist."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DirectoryProvider(ABC):
    name: str
    requires_credential: str

    @abstractmethod
    def enabled(self) -> bool:
        ...

    @abstractmethod
    def lookup_company(self, *, name: str | None = None, domain: str | None = None) -> dict[str, Any] | None:
        """Return attributed company fields or None. Never fabricate."""
        ...


class CrunchbaseProvider(DirectoryProvider):
    name = "crunchbase"
    requires_credential = "CRUNCHBASE_API_KEY"

    def enabled(self) -> bool:
        import os

        return bool(os.getenv("CRUNCHBASE_API_KEY") or os.getenv("CRUNCHBASE_API_KEY"))

    def lookup_company(self, *, name: str | None = None, domain: str | None = None) -> dict[str, Any] | None:
        if not self.enabled():
            return None
        return None  # licensed — wire when credential approved


class PeopleDataLabsProvider(DirectoryProvider):
    name = "people_data_labs"
    requires_credential = "PEOPLE_DATA_LABS_API_KEY"

    def enabled(self) -> bool:
        import os

        return bool(os.getenv("PEOPLE_DATA_LABS_API_KEY") or os.getenv("PDL_API_KEY"))

    def lookup_company(self, *, name: str | None = None, domain: str | None = None) -> dict[str, Any] | None:
        if not self.enabled():
            return None
        return None


class ClearbitProvider(DirectoryProvider):
    name = "clearbit"
    requires_credential = "CLEARBIT_API_KEY"

    def enabled(self) -> bool:
        import os

        return bool(os.getenv("CLEARBIT_API_KEY"))

    def lookup_company(self, *, name: str | None = None, domain: str | None = None) -> dict[str, Any] | None:
        if not self.enabled():
            return None
        return None


class ApolloProvider(DirectoryProvider):
    name = "apollo"
    requires_credential = "APOLLO_API_KEY"

    def enabled(self) -> bool:
        import os

        return bool(os.getenv("APOLLO_API_KEY"))

    def lookup_company(self, *, name: str | None = None, domain: str | None = None) -> dict[str, Any] | None:
        if not self.enabled():
            return None
        return None


class OpenCorporatesProvider(DirectoryProvider):
    name = "opencorporates"
    requires_credential = "OPENCORPORATES_API_TOKEN"

    def enabled(self) -> bool:
        import os

        return bool(os.getenv("OPENCORPORATES_API_TOKEN"))

    def lookup_company(self, *, name: str | None = None, domain: str | None = None) -> dict[str, Any] | None:
        if not self.enabled():
            return None
        return None


class CompaniesHouseProvider(DirectoryProvider):
    name = "companies_house"
    requires_credential = "COMPANIES_HOUSE_API_KEY"

    def enabled(self) -> bool:
        import os

        return bool(os.getenv("COMPANIES_HOUSE_API_KEY"))

    def lookup_company(self, *, name: str | None = None, domain: str | None = None) -> dict[str, Any] | None:
        if not self.enabled():
            return None
        return None


class SecDirectoryProvider(DirectoryProvider):
    name = "sec"
    requires_credential = ""  # public EDGAR — already collected via sec_edgar

    def enabled(self) -> bool:
        return True

    def lookup_company(self, *, name: str | None = None, domain: str | None = None) -> dict[str, Any] | None:
        return None


DIRECTORY_PROVIDERS: list[DirectoryProvider] = [
    CrunchbaseProvider(),
    PeopleDataLabsProvider(),
    ClearbitProvider(),
    ApolloProvider(),
    OpenCorporatesProvider(),
    CompaniesHouseProvider(),
    SecDirectoryProvider(),
]


def provider_status() -> list[dict[str, Any]]:
    return [
        {
            "name": p.name,
            "requires": p.requires_credential or None,
            "enabled": p.enabled(),
            "status": "ready" if p.enabled() else "missing_credential",
        }
        for p in DIRECTORY_PROVIDERS
    ]
