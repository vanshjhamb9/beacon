"""Domain intelligence — MX/DNS/SSL checks increase trust; never invent identity."""

from __future__ import annotations

import socket
import ssl
from datetime import UTC, datetime
from typing import Any

from identity_coverage.models.types import CoverageEvidence, UNKNOWN


def _now() -> str:
    return datetime.now(UTC).isoformat()


class DomainIntelligenceEngine:
    name = "domain_intelligence"
    priority = 35

    def collect(self, payload: dict[str, Any], *, probe: bool = True) -> list[CoverageEvidence]:
        domain = (
            payload.get("official_domain")
            or payload.get("domain")
            or (payload.get("metadata") or {}).get("official_domain")
        )
        if not domain:
            website = payload.get("official_website") or payload.get("website")
            if website:
                domain = str(website).replace("https://", "").replace("http://", "").split("/")[0]
        domain = str(domain or "").lower().removeprefix("www.")
        if not domain or "." not in domain:
            return []

        out: list[CoverageEvidence] = [
            CoverageEvidence(
                field="domain",
                value=domain,
                confidence=90.0,
                collector=str(payload.get("source") or UNKNOWN),
                timestamp=_now(),
                verification=True,
                source=self.name,
                priority=self.priority,
                reason="domain_present",
                evidence=[f"domain:{domain}"],
            )
        ]
        if not probe:
            return out

        # DNS A
        try:
            socket.getaddrinfo(domain, 443)
            out.append(
                CoverageEvidence(
                    field="dns_ok",
                    value="true",
                    confidence=85.0,
                    collector=str(payload.get("source") or UNKNOWN),
                    timestamp=_now(),
                    verification=True,
                    source=self.name,
                    priority=self.priority,
                    reason="dns_a_resolves",
                    evidence=[f"domain:{domain}"],
                )
            )
        except OSError:
            out.append(
                CoverageEvidence(
                    field="dns_ok",
                    value="false",
                    confidence=90.0,
                    collector=str(payload.get("source") or UNKNOWN),
                    timestamp=_now(),
                    verification=True,
                    source=self.name,
                    priority=self.priority,
                    reason="dns_a_failed",
                    evidence=[f"domain:{domain}"],
                )
            )

        # SSL handshake
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=4.0) as sock:
                with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    out.append(
                        CoverageEvidence(
                            field="ssl_ok",
                            value="true",
                            confidence=88.0,
                            collector=str(payload.get("source") or UNKNOWN),
                            timestamp=_now(),
                            verification=True,
                            source=self.name,
                            priority=self.priority,
                            reason="ssl_handshake_ok",
                            evidence=[f"subject:{cert.get('subject')}"],
                        )
                    )
        except Exception:  # noqa: BLE001
            out.append(
                CoverageEvidence(
                    field="ssl_ok",
                    value="false",
                    confidence=80.0,
                    collector=str(payload.get("source") or UNKNOWN),
                    timestamp=_now(),
                    verification=True,
                    source=self.name,
                    priority=self.priority,
                    reason="ssl_handshake_failed",
                    evidence=[f"domain:{domain}"],
                )
            )

        # MX via dnspython if available; else skip inventing
        try:
            import dns.resolver  # type: ignore

            answers = dns.resolver.resolve(domain, "MX")
            mx = [str(r.exchange).rstrip(".") for r in answers][:3]
            if mx:
                out.append(
                    CoverageEvidence(
                        field="mx",
                        value=",".join(mx),
                        confidence=86.0,
                        collector=str(payload.get("source") or UNKNOWN),
                        timestamp=_now(),
                        verification=True,
                        source=self.name,
                        priority=self.priority,
                        reason="mx_records",
                        evidence=mx,
                    )
                )
        except Exception:  # noqa: BLE001
            pass
        return out
