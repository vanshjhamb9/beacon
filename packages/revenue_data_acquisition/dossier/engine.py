"""Company dossier — one executive summary from attributed fields."""

from __future__ import annotations

from typing import Any

from revenue_data_acquisition.models.types import AttributedValue, CompanyDossier, UNKNOWN
from revenue_execution_validation.revenue_ready.engine import RevenueReadyDefinitionEngine


class CompanyDossierEngine:
    def __init__(self) -> None:
        self.rev = RevenueReadyDefinitionEngine()

    def build(
        self,
        *,
        company_id: str | None,
        identity: dict[str, Any],
        website: str | None,
        domain: str | None,
        emails: list[AttributedValue],
        decision_makers: list[dict[str, Any]],
        payload: dict[str, Any],
        collector: str = UNKNOWN,
    ) -> CompanyDossier:
        meta = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
        signals = list(meta.get("buying_signals") or payload.get("buying_signals") or [])
        # Attribute launch intent from real collector signals only — never invent.
        title = str(payload.get("title") or "").strip()
        if not signals and collector == "product_hunt" and title:
            signals = [f"Product Hunt launch signal: {title}"]
        if not signals and collector in {"github_trending", "github"} and title:
            signals = [f"GitHub identity signal: {title}"]
        tech = []
        if meta.get("language"):
            tech.append(str(meta["language"]))
        if meta.get("topic"):
            tech.append(str(meta["topic"]))

        website_attr = None
        if website and domain:
            website_attr = AttributedValue(
                value=website,
                source="official_website",
                collector=collector,
                confidence=95.0,
                verified=True,
                evidence=[f"domain:{domain}"],
            )

        rev_payload = {
            "company_id": company_id,
            "company_name": identity.get("trade_name") or identity.get("legal_name"),
            "website": website,
            "official_website": website,
            "domain": domain,
            "industry": identity.get("industry") or "Software",
            "description": identity.get("description") or "",
            "business_email": emails[0].value if emails else None,
            "decision_maker": (
                f"{decision_makers[0]['name']} ({decision_makers[0].get('role')})" if decision_makers else None
            ),
            "buying_signals": signals,
            "best_service": meta.get("recommended_service") or "AI Automation Platform",
            "service_matches": [{"service": meta.get("recommended_service") or "AI Automation Platform"}],
            "why_now": meta.get("why_now") or ("; ".join(signals[:3]) if signals else None),
            "opportunity": meta.get("opportunity"),
            "confidence": 80 if emails and decision_makers and website else 50,
            "erowd_verified": bool(website),
            "erowd_admitted": bool(website),
            "source": collector,
            "evidence": [f"website:{website}"] if website else [],
            "cir_classification": "Revenue Ready" if emails and decision_makers and website and signals else "UNKNOWN",
        }
        check = self.rev.evaluate(rev_payload)
        sales_ready = bool(website and emails and decision_makers and signals)
        trust = min(
            99.0,
            (40.0 if website else 0)
            + (25.0 if emails else 0)
            + (20.0 if decision_makers else 0)
            + (10.0 if signals else 0)
            + (5.0 if identity.get("description") else 0),
        )
        timeline = []
        if website:
            timeline.append(f"Official website verified: {website}")
        for e in emails[:2]:
            timeline.append(f"Business email recovered: {e.value}")
        for dm in decision_makers[:2]:
            timeline.append(f"Decision maker: {dm.get('name')} ({dm.get('role')}) via {dm.get('url')}")
        return CompanyDossier(
            company_id=company_id,
            identity={
                "legal_name": identity.get("legal_name"),
                "trade_name": identity.get("trade_name"),
                "aliases": identity.get("aliases") or [],
                "industry": identity.get("industry"),
                "country": identity.get("country"),
                "linkedin": identity.get("linkedin"),
            },
            website=website_attr,
            business={"description": identity.get("description")},
            buying_signals=signals,
            technology=tech,
            contacts=emails,
            decision_makers=decision_makers,
            service_match=check.best_service if hasattr(check, "best_service") else rev_payload["best_service"],
            evidence_timeline=timeline,
            trust_score=trust,
            sales_ready=sales_ready,
            revenue_ready=bool(check.is_revenue_ready),
        )
