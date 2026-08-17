"""Base collector for cybersecurity signal sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx


@dataclass
class RawSignal:
    """A raw signal from a source before classification."""
    source: str
    source_tier: int  # 1=direct, 2=strong, 3=discovery
    url: str
    title: str
    content: str
    author: str = ""
    author_url: str = ""
    published_at: datetime | None = None
    score: int = 0
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseCybersecurityCollector(ABC):
    """Base class for cybersecurity signal collectors."""

    source_name: str = ""
    source_tier: int = 3
    max_items: int = 50

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self.http_client = http_client

    @abstractmethod
    async def collect(self) -> Sequence[RawSignal]:
        """Collect raw signals from this source."""
        raise NotImplementedError

    def _is_relevant(self, text: str) -> bool:
        """Quick relevance check before full signal detection."""
        text_lower = text.lower()
        security_keywords = [
            "penetration test", "pentest", "vapt", "vulnerability",
            "security audit", "security test", "security assessment",
            "rfp", "tender", "procurement", "compliance", "soc 2",
            "iso 27001", "pci dss", "hipaa", "breach", "incident",
            "remediation", "retesting", "web app security", "api security",
            "mobile security", "cloud security", "network security",
            "ethical hacker", "bug bounty", "security team",
        ]
        return any(kw in text_lower for kw in security_keywords)
