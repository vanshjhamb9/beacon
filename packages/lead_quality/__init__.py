"""Lead Quality Score (LQS) — CTO bar for perfect outbound leads.

Hard rules:
- Directory sources never qualify
- Content age must be ≤ 48h
- Why-now must be a real trigger (not portfolio membership)
- Perfect outbound requires LQS ≥ PERFECT_THRESHOLD
- Visible outbound requires LQS ≥ OUTBOUND_THRESHOLD
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from collectors.freshness import (
    DIRECTORY_SOURCES,
    FRESH_HOURS,
    NEWS_OR_PLATFORM_HOSTS,
    age_hours,
    content_occurred_at,
    is_directory_source,
    passes_freshness_gate,
    why_now_is_stale,
)

SCORING_VERSION = "lqs-v1"
OUTBOUND_THRESHOLD = 78.0
PERFECT_THRESHOLD = 85.0

TRIGGER_STRENGTH = {
    "product_hunt": 22.0,
    "launch": 20.0,
    "funding": 18.0,
    "hiring": 16.0,
    "sec_edgar": 15.0,
    "hacker_news": 14.0,
    "reddit": 10.0,
    "github_trending": 8.0,
}


@dataclass
class LeadQualityResult:
    total: float
    freshness: float
    trigger: float
    identity: float
    contactability: float
    evidence: float
    penalties: float
    grade: str
    outbound_ready: bool
    perfect: bool
    pipeline_worthy: bool = False
    blockers: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    age_hours: float | None = None
    scoring_version: str = SCORING_VERSION

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class LeadQualityScorer:
    """Compose freshness-first quality for outbound prioritization."""

    def score(self, payload: dict[str, Any]) -> LeadQualityResult:
        attrs = dict(payload.get("attributes") or {})
        source = str(payload.get("source") or attrs.get("source") or "").lower()
        blockers: list[str] = []
        reasons: list[str] = []

        fresh_ok, fresh_reason, hours = passes_freshness_gate(
            source=source,
            published_at=payload.get("published_at") or payload.get("timestamp"),
            metadata=attrs,
            payload=payload,
            max_age_hours=FRESH_HOURS,
        )
        if not fresh_ok:
            blockers.append(fresh_reason)
        if is_directory_source(source, attrs) or source in DIRECTORY_SOURCES:
            blockers.append("directory_source")

        why = str(payload.get("why_now") or attrs.get("rrp_why_now") or attrs.get("why_now") or "")
        if why_now_is_stale(why) or "insufficient why-now" in why.lower():
            blockers.append("stale_or_missing_why_now")

        if payload.get("article_only") and not (
            payload.get("website") or payload.get("official_website") or attrs.get("official_website")
        ):
            # Soft penalty only — PH/HN often need a second-pass website recover
            reasons.append("needs_website_enrichment")

        freshness = self._freshness_points(hours if fresh_ok else None)
        trigger = self._trigger_points(payload, attrs, source)
        identity = self._identity_points(payload, attrs)
        contactability = self._contact_points(payload, attrs)
        evidence = self._evidence_points(payload, attrs)
        penalties = self._penalties(payload, attrs, source, blockers)

        total = round(
            max(0.0, min(100.0, freshness + trigger + identity + contactability + evidence - penalties)),
            2,
        )

        has_website = bool(
            payload.get("website")
            or payload.get("official_website")
            or attrs.get("official_website")
            or payload.get("primary_domain")
            or attrs.get("domain")
        )
        website_host = ""
        for cand in (
            payload.get("website"),
            payload.get("official_website"),
            attrs.get("official_website"),
            payload.get("primary_domain"),
            attrs.get("domain"),
        ):
            if not cand:
                continue
            raw = str(cand).lower().replace("https://", "").replace("http://", "").split("/")[0].removeprefix("www.")
            if raw:
                website_host = raw
                break
        if website_host and (
            website_host in NEWS_OR_PLATFORM_HOSTS
            or any(website_host.endswith("." + h) for h in NEWS_OR_PLATFORM_HOSTS)
        ):
            blockers.append("news_or_platform_host")
            has_website = False

        if not has_website:
            blockers.append("missing_website")

        if freshness < 15:
            blockers.append("weak_freshness")
        if trigger < 8:
            blockers.append("weak_trigger")
        if identity < 10:
            blockers.append("weak_identity")

        # Hard fail: critical blockers cap score and block outbound
        critical = {
            "directory_source",
            "directory_source_not_lead",
            "stale_signal",
            "stale_or_missing_why_now",
            "missing_content_timestamp",
            "missing_website",
            "news_or_platform_host",
        }
        hard_blocked = bool(critical.intersection(blockers))
        if hard_blocked:
            total = min(total, 49.0)

        # Pipeline fuel: fresh event triggers worth enriching even before contacts
        pipeline_worthy = (
            fresh_ok
            and source not in DIRECTORY_SOURCES
            and trigger >= 10
            and "stale_or_missing_why_now" not in blockers
            and "directory_source" not in blockers
        )

        outbound = (
            (not hard_blocked)
            and total >= OUTBOUND_THRESHOLD
            and has_website
            and contactability >= 8  # at least a same-org business email
        )
        perfect = (
            outbound
            and total >= PERFECT_THRESHOLD
            and identity >= 18
            and contactability >= 12
            and freshness >= 20
            and trigger >= 12
        )

        if outbound:
            reasons.append(f"LQS {total} >= outbound {OUTBOUND_THRESHOLD}")
        if perfect:
            reasons.append(f"LQS {total} >= perfect {PERFECT_THRESHOLD}")
        if pipeline_worthy:
            reasons.append("pipeline_worthy")
        if hours is not None:
            reasons.append(f"age_hours={round(hours, 1)}")
        reasons.append(f"trigger={trigger}")
        reasons.append(f"freshness={freshness}")

        grade = self._grade(total, hard_blocked)
        return LeadQualityResult(
            total=total,
            freshness=freshness,
            trigger=trigger,
            identity=identity,
            contactability=contactability,
            evidence=evidence,
            penalties=penalties,
            grade=grade,
            outbound_ready=outbound,
            perfect=perfect,
            pipeline_worthy=pipeline_worthy,
            blockers=sorted(set(blockers)),
            reasons=reasons,
            age_hours=hours,
        )

    def _freshness_points(self, hours: float | None) -> float:
        # Max 30 — freshness is the primary quality dimension
        if hours is None:
            return 0.0
        if hours <= 6:
            return 30.0
        if hours <= 12:
            return 27.0
        if hours <= 24:
            return 24.0
        if hours <= 36:
            return 20.0
        if hours <= 48:
            return 16.0
        return 0.0

    def _trigger_points(self, payload: dict[str, Any], attrs: dict[str, Any], source: str) -> float:
        # Max 25
        signals = list(payload.get("buying_signals") or attrs.get("buying_signals") or [])
        blob = " ".join(
            [
                str(payload.get("why_now") or ""),
                str(payload.get("title") or ""),
                str(payload.get("content") or ""),
                " ".join(str(s) for s in signals),
                source,
            ]
        ).lower()

        score = 0.0
        if "product hunt" in blob or source == "product_hunt":
            score = max(score, TRIGGER_STRENGTH["product_hunt"])
        if any(k in blob for k in ("launch", "launched", "shipping", "release")):
            score = max(score, TRIGGER_STRENGTH["launch"])
        if any(k in blob for k in ("funding", "raised", "series ", "seed")):
            score = max(score, TRIGGER_STRENGTH["funding"])
        if any(k in blob for k in ("hiring", "we're hiring", "job", "career")):
            score = max(score, TRIGGER_STRENGTH["hiring"])
        if source == "sec_edgar" or "edgar" in blob or "8-k" in blob:
            score = max(score, TRIGGER_STRENGTH["sec_edgar"])
        if source == "hacker_news":
            score = max(score, TRIGGER_STRENGTH["hacker_news"])
        if source == "reddit":
            score = max(score, TRIGGER_STRENGTH["reddit"])
        if source == "github_trending":
            score = max(score, TRIGGER_STRENGTH["github_trending"])
        if signals:
            score = min(25.0, score + min(5.0, len(signals) * 1.5))
        return min(25.0, score)

    def _identity_points(self, payload: dict[str, Any], attrs: dict[str, Any]) -> float:
        # Max 20
        pts = 0.0
        name = payload.get("company_name") or payload.get("company") or payload.get("name")
        if name and str(name).strip() not in {"", "UNKNOWN", "—"}:
            pts += 6.0
        website = (
            payload.get("official_website")
            or payload.get("website")
            or attrs.get("official_website")
            or payload.get("primary_domain")
            or attrs.get("domain")
        )
        if website:
            pts += 8.0
        if payload.get("website_verified") or attrs.get("erowd_verified"):
            pts += 4.0
        industry = payload.get("industry") or attrs.get("industry")
        if industry and str(industry) not in {"", "UNKNOWN", "—"}:
            pts += 2.0
        return min(20.0, pts)

    def _contact_points(self, payload: dict[str, Any], attrs: dict[str, Any]) -> float:
        # Max 15
        pts = 0.0
        email = (
            payload.get("business_email")
            or payload.get("verified_email")
            or payload.get("email")
            or attrs.get("business_email")
        )
        if email and "@" in str(email) and "noreply" not in str(email).lower():
            pts += 8.0
        dm = payload.get("decision_maker") or attrs.get("decision_maker")
        if dm and str(dm).lower() not in {"", "unknown", "—", "none"}:
            pts += 7.0
        return min(15.0, pts)

    def _evidence_points(self, payload: dict[str, Any], attrs: dict[str, Any]) -> float:
        # Max 10
        evidence = list(payload.get("evidence") or attrs.get("evidence") or [])
        signals = list(payload.get("buying_signals") or attrs.get("buying_signals") or [])
        pts = min(6.0, len(evidence) * 2.0) + min(4.0, len(signals) * 1.5)
        if payload.get("description") or attrs.get("description"):
            pts = min(10.0, pts + 2.0)
        return min(10.0, pts)

    def _penalties(
        self,
        payload: dict[str, Any],
        attrs: dict[str, Any],
        source: str,
        blockers: list[str],
    ) -> float:
        penalty = 0.0
        if payload.get("article_only"):
            penalty += 8.0
        if source in DIRECTORY_SOURCES:
            penalty += 40.0
        if "stale_or_missing_why_now" in blockers:
            penalty += 15.0
        if payload.get("is_news") or attrs.get("is_news"):
            penalty += 6.0
        return penalty

    def _grade(self, total: float, hard_blocked: bool) -> str:
        if hard_blocked or total < 50:
            return "F"
        if total >= PERFECT_THRESHOLD:
            return "A"
        if total >= OUTBOUND_THRESHOLD:
            return "B"
        if total >= 65:
            return "C"
        return "D"


def is_perfect_lead(payload: dict[str, Any]) -> bool:
    return LeadQualityScorer().score(payload).perfect


def is_outbound_ready(payload: dict[str, Any]) -> bool:
    return LeadQualityScorer().score(payload).outbound_ready


def annotate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = LeadQualityScorer().score(payload)
    out = dict(payload)
    out["lead_quality_score"] = result.total
    out["lead_quality"] = result.as_dict()
    out["outbound_ready"] = result.outbound_ready
    out["perfect_lead"] = result.perfect
    return out
