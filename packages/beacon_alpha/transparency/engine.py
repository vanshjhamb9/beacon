from __future__ import annotations

from typing import Any

from beacon_alpha.models.types import SourceTransparency, UNKNOWN


class SourceTransparencyEngine:
    """Rule 7 — visible provenance on every company."""

    def build(self, payload: dict[str, Any]) -> SourceTransparency:
        collected_from = str(payload.get("collected_from") or payload.get("source") or UNKNOWN)
        collector = str(payload.get("collector") or payload.get("collector_name") or payload.get("source") or UNKNOWN)
        date = payload.get("collected_at") or payload.get("date") or payload.get("last_seen_at")
        url = str(payload.get("original_url") or payload.get("source_url") or payload.get("url") or UNKNOWN)
        title = str(payload.get("original_post_title") or payload.get("post_title") or payload.get("title") or UNKNOWN)

        snippets: list[str] = []
        for item in payload.get("evidence") or []:
            if isinstance(item, dict):
                snip = item.get("summary") or item.get("text") or item.get("snippet")
                if snip:
                    snippets.append(str(snip))
            elif isinstance(item, str):
                snippets.append(item)
        for row in payload.get("timeline") or []:
            if isinstance(row, dict) and row.get("summary"):
                snippets.append(str(row["summary"]))

        history = list(payload.get("verification_history") or [])
        if payload.get("mx_valid"):
            history.append("mx_validated")
        if payload.get("website_alive") or payload.get("website_verified"):
            history.append("website_verified")
        if payload.get("ssl"):
            history.append("ssl_ok")

        last_crawl = payload.get("last_crawl") or payload.get("last_crawled_at") or payload.get("collected_at")

        complete = all(
            [
                collected_from != UNKNOWN,
                collector != UNKNOWN,
                url != UNKNOWN or bool(payload.get("website")),
                len(snippets) > 0,
            ]
        )
        return SourceTransparency(
            collected_from=collected_from,
            collector=collector,
            date=date,
            original_url=url if url != UNKNOWN else str(payload.get("website") or UNKNOWN),
            original_post_title=title,
            evidence_snippets=snippets[:12],
            verification_history=[str(h) for h in history][:20],
            last_crawl=last_crawl,
            complete=complete,
            evidence=[f"transparency:{'complete' if complete else 'partial'}", f"snippets:{len(snippets)}"],
        )
