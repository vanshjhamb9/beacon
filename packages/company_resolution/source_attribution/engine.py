"""Phase 5 — every company remembers which signal created it."""

from __future__ import annotations

from company_resolution.models.types import RawSignalEnvelope, SourceAttribution, UNKNOWN


class SourceAttributionEngine:
    def attribute(self, signal: RawSignalEnvelope) -> SourceAttribution:
        url = signal.url
        source = (signal.source or UNKNOWN).lower()
        evidence = [f"source:{source}", f"signal:{signal.signal_id}"]
        if url:
            evidence.append(f"url:{url}")

        return SourceAttribution(
            signal_id=signal.signal_id,
            source=source,
            source_url=url,
            article_url=url if source in {"rss", "devto"} else None,
            reddit_thread=url if source == "reddit" else None,
            product_hunt_page=url if source == "product_hunt" else None,
            devto_article=url if source == "devto" else None,
            hn_item=url if source in {"hacker_news", "hn"} else None,
            collected_at=signal.timestamp,
            complete=bool(signal.signal_id and signal.signal_id != UNKNOWN and source != UNKNOWN and url),
            evidence=evidence,
        )
