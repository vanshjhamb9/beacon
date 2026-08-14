"""Company identity expansion from attributed website evidence."""

from __future__ import annotations

from typing import Any

from identity_coverage.website_intel.engine import WebsiteIntelligenceEngine
from revenue_data_acquisition.models.types import AttributedValue, UNKNOWN


class CompanyIdentityExpansionEngine:
    def __init__(self) -> None:
        self.website = WebsiteIntelligenceEngine()

    def expand(self, payload: dict[str, Any], *, crawl_website: bool = False) -> dict[str, Any]:
        website = payload.get("official_website") or payload.get("website")
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        hints = list(meta.get("company_hints") or [])
        legal = payload.get("title") or (hints[0] if hints else None)
        out: dict[str, Any] = {
            "legal_name": legal,
            "trade_name": None,
            "aliases": hints[:8],
            "industry": payload.get("industry") or meta.get("industry"),
            "country": payload.get("country") or meta.get("country"),
            "description": payload.get("description") or meta.get("description") or meta.get("about"),
            "linkedin": meta.get("linkedin_company") or meta.get("linkedin"),
            "github": meta.get("github_organization"),
            "twitter": meta.get("twitter"),
            "attribution": [],
        }
        if out["legal_name"]:
            out["trade_name"] = out["legal_name"]
            out["attribution"].append(
                AttributedValue(
                    value=str(out["legal_name"]),
                    source="signal",
                    collector=str(payload.get("source") or UNKNOWN),
                    confidence=70.0,
                    verified=False,
                    evidence=["signal_title_or_hint"],
                ).model_dump()
            )
        # Optional crawl only — default off for compose/deterministic evaluate paths
        if website and crawl_website:
            for ev in self.website.collect({**payload, "official_website": website}):
                if ev.field == "linkedin_company" and not out["linkedin"]:
                    out["linkedin"] = ev.value
                if ev.field == "open_graph" and not out["description"]:
                    out["description"] = ev.value[:500]
                if ev.field == "schema_org":
                    out["attribution"].append(ev.model_dump())
        # Never invent employees/founded
        out["employees"] = meta.get("employees") if meta.get("employees_verified") else None
        out["founded"] = meta.get("founded") if meta.get("founded_verified") else None
        return out
