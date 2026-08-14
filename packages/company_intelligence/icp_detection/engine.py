"""ICP Detection — who does this company sell to? Evidence required."""

from __future__ import annotations

from typing import Any

from company_intelligence.models.types import UNKNOWN, AttributedValue, IcpProfile, WebsiteCorpus

ICP_RULES: tuple[tuple[str, tuple[str, ...], float], ...] = (
    ("Enterprise", ("enterprise", "fortune 500", "large organizations", "global companies"), 90),
    ("SMB", ("smb", "small business", "small teams", "startups and smbs"), 85),
    ("Mid Market", ("mid-market", "mid market", "growing companies"), 80),
    ("Government", ("government", "public sector", "federal", "municipal"), 88),
    ("Healthcare", ("hospitals", "clinics", "providers", "healthcare organizations"), 86),
    ("Finance", ("banks", "financial institutions", "fintech companies", "insurers"), 86),
    ("Education", ("schools", "universities", "educators", "students"), 84),
    ("Automotive", ("automotive", "dealerships", "fleet"), 80),
    ("Manufacturing", ("manufacturers", "factories", "plants"), 82),
    ("Real Estate", ("brokers", "property managers", "real estate agents"), 80),
    ("Retail", ("retailers", "stores", "merchants", "ecommerce brands"), 82),
    ("Agencies", ("agencies", "marketing agencies", "consultancies"), 80),
    ("Developers", ("developers", "engineering teams", "dev teams", "api-first"), 85),
    ("Consumers", ("consumers", "individuals", "personal use", "b2c"), 78),
)


class IcpDetectionEngine:
    def detect(self, corpus: WebsiteCorpus, payload: dict[str, Any] | None = None) -> IcpProfile:
        payload = payload or {}
        blob = " ".join(
            [
                str(payload.get("description") or ""),
                *[f"{p.title} {' '.join(p.headings)} {p.text[:2500]}" for p in corpus.pages],
            ]
        ).lower()

        segments: list[AttributedValue] = []
        for label, terms, conf in ICP_RULES:
            hit = next((t for t in terms if t in blob), None)
            if hit:
                segments.append(
                    AttributedValue(
                        value=label,
                        confidence=conf,
                        source="keyword_evidence",
                        excerpt=hit,
                        evidence=[f"term:{hit}", f"icp:{label}"],
                    )
                )

        if payload.get("icp"):
            segments.insert(
                0,
                AttributedValue(
                    value=str(payload["icp"]),
                    confidence=92,
                    source="payload",
                    excerpt=str(payload["icp"]),
                    evidence=[f"payload_icp:{payload['icp']}"],
                ),
            )

        # Dedupe by value
        seen: set[str] = set()
        unique: list[AttributedValue] = []
        for s in segments:
            if s.value in seen:
                continue
            seen.add(s.value)
            unique.append(s)

        primary = unique[0] if unique else AttributedValue()
        confidence = primary.confidence if primary.value != UNKNOWN else 0.0
        return IcpProfile(
            segments=unique[:8],
            primary_icp=primary,
            confidence=confidence,
            evidence=[f"segments:{len(unique)}", f"primary:{primary.value}"],
        )
