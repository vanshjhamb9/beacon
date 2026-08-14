"""Revenue Ready definition — compose checks from existing CIR/EROWD/attrs. Never fabricate."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any  # noqa: I001
from urllib.parse import urlparse

from collectors.freshness import (
    DIRECTORY_SOURCES,
    FRESH_HOURS,
    passes_freshness_gate,
    why_now_is_stale,
)
from lead_quality import LeadQualityScorer, OUTBOUND_THRESHOLD
from revenue_execution_validation.models.types import (
    UNKNOWN,
    EvidenceItem,
    RejectionReason,
    RevenueReadyCheck,
)

INTENT_CUES = (
    "hiring",
    "launched",
    "product hunt",
    "funding",
    "series ",
    "ai adoption",
    "automation",
    "scaling",
    "saas",
    "ecommerce",
    "expansion",
    "growing",
)

DIRECTORY_INTENT_NOISE = (
    "yc company directory",
    "yc portfolio",
    "app store listing",
    "google play listing",
)

PLATFORM_HOSTS = frozenset(
    {
        "producthunt.com",
        "github.com",
        "reddit.com",
        "news.ycombinator.com",
        "medium.com",
        "techcrunch.com",
        "dev.to",
    }
)


class RevenueReadyDefinitionEngine:
    """ALL conditions must be true for Revenue Ready."""

    def evaluate(self, payload: dict[str, Any]) -> RevenueReadyCheck:
        attrs = dict(payload.get("attributes") or {})
        card = dict(payload.get("cir_founder_card") or attrs.get("cir_founder_card") or {})
        narrative = dict(payload.get("cir_narrative") or attrs.get("cir_narrative") or {})

        name = str(payload.get("company_name") or payload.get("name") or card.get("company") or UNKNOWN).strip()
        website = str(
            payload.get("official_website")
            or payload.get("website")
            or attrs.get("official_website")
            or card.get("website")
            or UNKNOWN
        ).strip()
        domain = str(payload.get("domain") or attrs.get("domain") or UNKNOWN).strip().lower().removeprefix("www.")
        if domain == UNKNOWN and website not in {"", UNKNOWN}:
            domain = urlparse(website if "://" in website else f"https://{website}").netloc.lower().removeprefix("www.") or UNKNOWN

        country = str(payload.get("country") or card.get("country") or attrs.get("country") or UNKNOWN)
        industry = str(payload.get("industry") or card.get("industry") or attrs.get("industry") or UNKNOWN)
        description = str(
            payload.get("description")
            or attrs.get("description")
            or card.get("primary_product")
            or UNKNOWN
        )
        email = str(
            payload.get("business_email")
            or card.get("business_email")
            or payload.get("email")
            or attrs.get("business_email")
            or UNKNOWN
        )
        dm_raw: Any = payload.get("decision_maker") or attrs.get("decision_maker")
        if not dm_raw and isinstance(card.get("decision_makers"), list) and card.get("decision_makers"):
            dm_raw = card["decision_makers"][0]
        if isinstance(dm_raw, list):
            dm_raw = dm_raw[0] if dm_raw else UNKNOWN
        dm = str(dm_raw or UNKNOWN)
        best_service = str(
            payload.get("best_service")
            or card.get("best_service")
            or attrs.get("cir_best_service")
            or narrative.get("which_service")
            or UNKNOWN
        )
        why_now = str(payload.get("why_now") or narrative.get("why_now") or card.get("recommended_action") or UNKNOWN)
        opportunity = str(payload.get("opportunity") or narrative.get("what_opportunity") or card.get("primary_opportunity") or UNKNOWN)
        source = str(payload.get("source") or attrs.get("source") or UNKNOWN)
        confidence = float(payload.get("confidence") or attrs.get("cir_readiness_score") or card.get("readiness_score") or 0)

        erowd = bool(payload.get("erowd_admitted") or payload.get("erowd_verified") or attrs.get("erowd_verified") or attrs.get("erowd_admitted"))
        website_verified = bool(
            payload.get("website_verified")
            or attrs.get("erowd_verified")
            or (website not in {"", UNKNOWN} and domain not in {"", UNKNOWN} and domain not in PLATFORM_HOSTS)
        )

        raw_signals = list(
            payload.get("buying_signals") or attrs.get("cir_buying_signals") or card.get("buying_signals") or []
        )
        signals = [
            s
            for s in raw_signals
            if not any(noise in str(s).lower() for noise in DIRECTORY_INTENT_NOISE)
        ]
        blob = " ".join(
            [
                str(description).lower(),
                str(why_now).lower(),
                " ".join(str(s).lower() for s in signals),
                str(payload.get("content") or "").lower(),
            ]
        )
        intent = (
            bool(signals)
            or any(c in blob for c in INTENT_CUES)
            or str(payload.get("source") or "").lower() == "product_hunt"
        )
        if str(source).lower() in DIRECTORY_SOURCES and not signals:
            intent = False

        service_ok = best_service not in {"", UNKNOWN} and bool(
            payload.get("service_match_evidence")
            or attrs.get("cir_best_service")
            or narrative.get("evidence")
            or (payload.get("service_matches") or [])
        )
        # If CIR classified Revenue Ready / Priority with a service, accept as evidenced match
        cir_class = str(attrs.get("cir_classification") or card.get("revenue_readiness") or payload.get("cir_classification") or "")
        if not service_ok and best_service not in {"", UNKNOWN} and cir_class in {"Revenue Ready", "Priority Account"}:
            service_ok = True

        email_ok = email not in {"", UNKNOWN} and "@" in email and not any(
            x in email.lower() for x in ("example.com", "sentry.io", "wixpress", "noreply")
        )
        dm_ok = dm not in {"", UNKNOWN} and "unknown" not in str(dm).lower()

        identity = all(
            [
                name not in {"", UNKNOWN},
                website not in {"", UNKNOWN},
                domain not in {"", UNKNOWN},
                country not in {"", UNKNOWN},
                industry not in {"", UNKNOWN},
                description not in {"", UNKNOWN},
                erowd or website_verified,
            ]
        )

        fresh_ok, fresh_reason, age_hours = passes_freshness_gate(
            source=source if source != UNKNOWN else str(attrs.get("source") or ""),
            published_at=payload.get("published_at")
            or payload.get("timestamp")
            or attrs.get("content_occurred_at")
            or attrs.get("launch_date"),
            metadata=attrs,
            payload=payload,
            max_age_hours=FRESH_HOURS,
        )
        why_ok = (
            why_now not in {"", UNKNOWN}
            and not why_now_is_stale(why_now)
            and "insufficient why-now" not in why_now.lower()
        )

        reasons: list[RejectionReason] = []
        if not erowd and not website_verified:
            reasons.append(RejectionReason.NOT_EROWD_ADMITTED)
        if website in {"", UNKNOWN} or domain in PLATFORM_HOSTS:
            if domain in PLATFORM_HOSTS:
                if "github" in domain:
                    reasons.append(RejectionReason.REPOSITORY_ONLY)
                else:
                    reasons.append(RejectionReason.PLATFORM_PAGE)
            else:
                reasons.append(RejectionReason.NO_WEBSITE)
        if payload.get("article_only") or payload.get("is_news"):
            reasons.append(RejectionReason.NEWS_ARTICLE)
        if payload.get("is_fake") or "test company" in name.lower():
            reasons.append(RejectionReason.FAKE_COMPANY)
        if payload.get("is_duplicate"):
            reasons.append(RejectionReason.DUPLICATE)
        if not identity:
            reasons.append(RejectionReason.IDENTITY_INCOMPLETE)
        if not intent:
            reasons.append(RejectionReason.NO_BUYING_INTENT)
        if not service_ok:
            reasons.append(RejectionReason.NO_SERVICE_MATCH)
        if not email_ok:
            reasons.append(RejectionReason.NO_BUSINESS_EMAIL)
        if confidence and confidence < 40 and not (identity and intent and service_ok and email_ok):
            reasons.append(RejectionReason.CONFIDENCE_TOO_LOW)
        if not (payload.get("evidence") or attrs.get("cir_evidence") or narrative.get("evidence") or signals):
            if RejectionReason.WEAK_EVIDENCE not in reasons and not (identity and intent and email_ok):
                reasons.append(RejectionReason.WEAK_EVIDENCE)
        if str(source).lower() in DIRECTORY_SOURCES or fresh_reason == "directory_source_not_lead":
            reasons.append(RejectionReason.DIRECTORY_SOURCE)
        if not fresh_ok and RejectionReason.DIRECTORY_SOURCE not in reasons:
            reasons.append(RejectionReason.STALE_SIGNAL)
        if not why_ok:
            reasons.append(RejectionReason.INSUFFICIENT_WHY_NOW)

        lqs = LeadQualityScorer().score(
            {
                **payload,
                "attributes": attrs,
                "source": source,
                "why_now": why_now,
                "buying_signals": signals,
                "published_at": payload.get("published_at")
                or payload.get("timestamp")
                or attrs.get("content_occurred_at")
                or attrs.get("launch_date"),
            }
        )
        lqs_ok = lqs.outbound_ready and lqs.total >= OUTBOUND_THRESHOLD
        if not lqs_ok:
            reasons.append(RejectionReason.LEAD_QUALITY_TOO_LOW)

        evidence_items = [
            EvidenceItem(
                source=source,
                timestamp=payload.get("timestamp") or datetime.now(UTC).isoformat(),
                url=website if website != UNKNOWN else str(payload.get("url") or UNKNOWN),
                why_qualifies=opportunity if opportunity != UNKNOWN else f"{name} identity+intent+service checks",
                why_now=why_now,
                confidence=confidence,
            )
        ]
        for s in signals[:5]:
            evidence_items.append(
                EvidenceItem(
                    source=source,
                    timestamp=datetime.now(UTC).isoformat(),
                    url=website,
                    why_qualifies=f"Buying signal: {s}",
                    why_now=str(s),
                    confidence=max(confidence, 70),
                )
            )

        evidence_ok = bool(evidence_items) and (
            identity or intent or service_ok or email_ok
        )

        is_ready = bool(
            identity
            and website_verified
            and intent
            and service_ok
            and email_ok
            and evidence_ok
            and fresh_ok
            and why_ok
            and lqs_ok
        )
        if is_ready:
            reasons = []

        return RevenueReadyCheck(
            is_revenue_ready=is_ready,
            identity_complete=identity,
            website_verified=website_verified,
            intent_detected=intent,
            service_match=service_ok,
            business_email=email_ok,
            decision_maker=dm_ok,
            evidence_ok=evidence_ok,
            company_name=name,
            website=website,
            domain=domain or UNKNOWN,
            country=country,
            industry=industry,
            description=description[:500] if description != UNKNOWN else UNKNOWN,
            email=email if email_ok else UNKNOWN,
            decision_maker_name=str(dm) if dm_ok else UNKNOWN,
            best_service=best_service,
            why_now=why_now,
            opportunity=opportunity,
            confidence=confidence,
            source=source,
            rejection_reasons=reasons,
            evidence=evidence_items,
            checks={
                "identity": identity,
                "website": website_verified,
                "intent": intent,
                "service_match": service_ok,
                "business_email": email_ok,
                "decision_maker": dm_ok,
                "evidence": evidence_ok,
                "erowd": erowd,
                "freshness": fresh_ok,
                "why_now": why_ok,
                "lead_quality": lqs_ok,
                "lqs_total": lqs.total,
                "lqs_grade": lqs.grade,
                "perfect_lead": lqs.perfect,
                "age_hours": age_hours,
                "freshness_reason": fresh_reason,
            },
        )
