from __future__ import annotations

import subprocess
from collections.abc import Callable

from lead_enrichment.connectors.website import normalize_domain
from lead_enrichment.models.types import DnsMxResult, EnrichmentOpportunityInput

MxResolver = Callable[[str], list[str]]

_PROVIDER_HINTS: tuple[tuple[str, str], ...] = (
    ("google", "Google Workspace"),
    ("googlemail", "Google Workspace"),
    ("outlook", "Microsoft 365"),
    ("protection.outlook", "Microsoft 365"),
    ("mimecast", "Mimecast"),
    ("zoho", "Zoho Mail"),
    ("protonmail", "Proton Mail"),
    ("fastmail", "Fastmail"),
)


def _default_mx_resolver(domain: str) -> list[str]:
    hosts: list[str] = []
    try:
        completed = subprocess.run(
            ["nslookup", "-type=MX", domain],
            check=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        for line in completed.stdout.splitlines():
            lowered = line.lower()
            if "mail exchanger" in lowered or "mx preference" in lowered:
                token = line.split("=")[-1].strip().rstrip(".").lower()
                if token and token not in hosts:
                    hosts.append(token)
    except (OSError, subprocess.TimeoutExpired):
        return []
    return hosts


class DnsMxConnector:
    name = "dns_mx"

    def __init__(self, *, resolver: MxResolver | None = None, enabled: bool = True) -> None:
        self.resolver = resolver or _default_mx_resolver
        self.enabled = enabled

    def collect(self, item: EnrichmentOpportunityInput) -> DnsMxResult | None:
        domain = normalize_domain(item.domain or item.website)
        if not self.enabled or not domain:
            return None
        try:
            mx_hosts = self.resolver(domain)
        except Exception:  # noqa: BLE001
            return DnsMxResult(domain=domain, mx_hosts=[], confidence=0.0)
        provider = None
        for host in mx_hosts:
            for needle, label in _PROVIDER_HINTS:
                if needle in host:
                    provider = label
                    break
            if provider:
                break
        confidence = 75.0 if mx_hosts else 0.0
        if provider:
            confidence = 88.0
        return DnsMxResult(
            domain=domain,
            mx_hosts=mx_hosts,
            mail_provider=provider,
            confidence=confidence,
        )
