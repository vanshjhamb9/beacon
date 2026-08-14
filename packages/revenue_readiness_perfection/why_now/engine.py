"""Why Now — only time-bounded trigger evidence. Directory membership is not urgency."""

from __future__ import annotations

from typing import Any

from collectors.freshness import why_now_is_stale


class WhyNowEngine:
    def build(self, *, signals: list[str], source: str, attrs: dict[str, Any], company: str) -> tuple[str, list[str]]:
        evidence: list[str] = []
        reasons: list[str] = []
        src = str(source or "").lower()

        for s in signals or []:
            text = str(s)
            low = text.lower()
            # Explicitly ignore directory / portfolio membership as why-now
            if why_now_is_stale(text) or "yc company directory" in low or "yc portfolio" in low:
                continue
            if "yc" in low and "hiring" in low:
                reasons.append(f"{company} shows a YC hiring flag — verify a recent open role before outreach")
                evidence.append(text)
            elif "product hunt" in low or "launch" in low:
                reasons.append("Recent product launch signal")
                evidence.append(text)
            elif "hiring" in low or "job" in low or "career" in low:
                reasons.append("Hiring / growth signal")
                evidence.append(text)
            elif "funding" in low or "raised" in low or "series" in low:
                reasons.append("Funding / capital event")
                evidence.append(text)
            elif "reddit" in low or "hacker news" in low or "hn " in low:
                reasons.append("Recent community traction signal")
                evidence.append(text)
            elif "filing" in low or "edgar" in low or "8-k" in low or "10-k" in low:
                reasons.append("Recent SEC filing activity")
                evidence.append(text)
            elif "app store" in low or "google play" in low:
                # Listing alone is not urgency
                continue
            else:
                reasons.append(text)
                evidence.append(text)

        # Source-level fallbacks for true event sources only
        if not reasons and src == "product_hunt":
            reasons.append(f"Recent Product Hunt launch for {company}")
            evidence.append("source:product_hunt")
        if not reasons and src in {"reddit", "hacker_news"}:
            reasons.append(f"Recent public discussion mentioning {company}")
            evidence.append(f"source:{src}")
        if not reasons and src == "sec_edgar":
            reasons.append(f"Recent SEC filing activity for {company}")
            evidence.append("source:sec_edgar")
        if not reasons and src == "github_trending":
            reasons.append(f"Recent GitHub activity for {company}")
            evidence.append("source:github_trending")

        # Never invent why-now from YC/App Store directory membership
        if not reasons and src in {"yc", "app_store", "google_play"}:
            return "Insufficient why-now evidence", ["directory_source_not_trigger"]

        why = reasons[0] if reasons else "Insufficient why-now evidence"
        if why_now_is_stale(why):
            return "Insufficient why-now evidence", evidence or ["stale_why_now_blocked"]
        return why, evidence
