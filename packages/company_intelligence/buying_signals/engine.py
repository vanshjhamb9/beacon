"""Buying Signal Engine — evidence-backed intent signals only."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from company_intelligence.models.types import BuyingSignal, WebsiteCorpus

SIGNAL_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Hiring", ("we're hiring", "now hiring", "open roles", "join our team", "careers")),
    ("AI Hiring", ("hiring ai", "ai engineer", "machine learning engineer", "llm engineer")),
    ("Engineering Hiring", ("hiring engineers", "software engineer", "backend engineer", "devops engineer")),
    ("Expansion", ("expanding", "new office", "opening in", "global expansion")),
    ("New Pricing", ("new pricing", "updated pricing", "price change")),
    ("Enterprise Launch", ("enterprise launch", "introducing enterprise", "enterprise plan")),
    ("Funding", ("raised", "series a", "series b", "seed round", "funding")),
    ("Product Launch", ("launched", "introducing", "now available", "product launch")),
    ("New Integrations", ("new integration", "now integrates", "integrates with")),
    ("API", ("public api", "api launch", "developer api", "rest api")),
    ("Migration", ("migrating", "migration", "moving from")),
    ("Scaling", ("scaling", "hypergrowth", "rapid growth")),
    ("Global Expansion", ("international", "worldwide", "global expansion")),
    ("Customer Growth", ("10,000 customers", "customers worldwide", "trusted by")),
    ("Security", ("soc 2", "iso 27001", "security compliance", "gdpr")),
    ("Compliance", ("hipaa", "compliance", "regulated")),
    ("Acquisition", ("acquired", "acquisition", "merger")),
)


class BuyingSignalEngine:
    def detect(self, corpus: WebsiteCorpus, payload: dict[str, Any] | None = None) -> list[BuyingSignal]:
        payload = payload or {}
        signals: list[BuyingSignal] = []
        now = datetime.now(UTC)

        pages = list(corpus.pages)
        if not pages and (payload.get("description") or payload.get("content")):
            from company_intelligence.models.types import WebsitePage

            pages = [
                WebsitePage(
                    url=str(payload.get("website") or "payload"),
                    path="/",
                    text=str(payload.get("description") or "") + " " + str(payload.get("content") or ""),
                    title=str(payload.get("company_name") or ""),
                )
            ]

        for page in pages:
            blob = f"{page.title} {' '.join(page.headings)} {page.text}".lower()
            for signal_type, terms in SIGNAL_RULES:
                term = next((t for t in terms if t in blob), None)
                if not term:
                    continue
                idx = blob.find(term)
                excerpt = blob[max(0, idx - 40) : idx + 120].strip()
                signals.append(
                    BuyingSignal(
                        signal_type=signal_type,
                        confidence=82.0 if signal_type in {"Hiring", "Funding", "Product Launch"} else 74.0,
                        source="website_page",
                        timestamp=now,
                        page=page.url,
                        excerpt=excerpt or term,
                        evidence=[f"term:{term}", f"page:{page.path}"],
                    )
                )

        for raw in payload.get("buying_signals") or []:
            if isinstance(raw, str):
                signals.append(
                    BuyingSignal(
                        signal_type=raw,
                        confidence=90.0,
                        source="payload",
                        timestamp=now,
                        excerpt=raw,
                        evidence=[f"payload:{raw}"],
                    )
                )
            elif isinstance(raw, dict) and raw.get("signal_type"):
                signals.append(
                    BuyingSignal(
                        signal_type=str(raw["signal_type"]),
                        confidence=float(raw.get("confidence") or 90),
                        source=str(raw.get("source") or "payload"),
                        timestamp=raw.get("timestamp") or now,
                        page=raw.get("page"),
                        excerpt=str(raw.get("excerpt") or raw["signal_type"]),
                        evidence=list(raw.get("evidence") or ["payload"]),
                    )
                )

        seen: set[str] = set()
        unique: list[BuyingSignal] = []
        for s in signals:
            if s.signal_type in seen:
                continue
            seen.add(s.signal_type)
            unique.append(s)
        return unique[:25]
