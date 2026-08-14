from __future__ import annotations

from typing import Any

from sales_readiness.models.types import WebsiteGrade, WebsiteIntelligence, UNKNOWN


class WebsiteIntelligenceEngine:
    """Deterministic website maturity / trust grade from observed profile signals."""

    def analyze(self, payload: dict[str, Any]) -> WebsiteIntelligence:
        evidence: list[str] = []
        score = 0.0

        has_website = bool(payload.get("website") or payload.get("primary_domain") or payload.get("domain"))
        if has_website:
            score += 25.0
            evidence.append("has_website")
        else:
            return WebsiteIntelligence(grade=WebsiteGrade.F, evidence=["no_website"])

        ssl = bool(payload.get("ssl") or payload.get("https") or True)
        if ssl:
            score += 10.0
            evidence.append("ssl")

        seo = float(payload.get("seo_score") or 0.0)
        score += min(15.0, seo / 100.0 * 15.0)
        if seo:
            evidence.append(f"seo:{seo}")

        chatbot = bool(payload.get("chatbot") or payload.get("has_chatbot"))
        pricing = payload.get("pricing_page") or payload.get("pricing")
        is_saas = payload.get("is_saas")
        if is_saas is None:
            techs = [str(t).lower() for t in (payload.get("technologies") or [])]
            is_saas = any(t in {"stripe", "segment", "intercom", "hubspot", "salesforce"} for t in techs)
        is_services = bool(payload.get("is_services"))
        if is_services is None:
            is_services = "agency" in str(payload.get("industry") or "").lower()

        if chatbot:
            score += 8.0
            evidence.append("chatbot")
        if pricing:
            score += 12.0
            evidence.append("pricing_present")
        if is_saas:
            score += 10.0
            evidence.append("saas_signals")
        if payload.get("careers_page") or payload.get("has_careers"):
            score += 8.0
            evidence.append("careers")
        if payload.get("blog") or payload.get("has_blog"):
            score += 5.0
            evidence.append("blog")
        if payload.get("enterprise") or payload.get("enterprise_page"):
            score += 7.0
            evidence.append("enterprise_page")

        mobile = float(payload.get("mobile_score") or 0.0)
        score += min(10.0, mobile / 100.0 * 10.0)

        score = min(100.0, round(score, 2))
        grade = self._grade(score)

        company_maturity = UNKNOWN
        product_maturity = UNKNOWN
        trust = UNKNOWN
        pricing_label = UNKNOWN
        enterprise = UNKNOWN
        if score >= 80:
            company_maturity, product_maturity, trust, pricing_label, enterprise = (
                "mature",
                "productized",
                "high",
                "public" if pricing else "unknown",
                "ready",
            )
        elif score >= 60:
            company_maturity, product_maturity, trust, pricing_label, enterprise = (
                "growing",
                "defined",
                "medium",
                "public" if pricing else "unknown",
                "partial",
            )
        elif score >= 40:
            company_maturity, product_maturity, trust = "early", "emerging", "low"
            pricing_label = "public" if pricing else "unknown"
            enterprise = "not_ready"
        else:
            company_maturity, product_maturity, trust, enterprise = "unclear", "unclear", "low", "not_ready"
            pricing_label = "public" if pricing else UNKNOWN

        return WebsiteIntelligence(
            grade=grade,
            company_maturity=company_maturity,
            product_maturity=product_maturity,
            trust=trust,
            pricing=pricing_label,
            is_saas=is_saas,
            is_services=is_services,
            enterprise_readiness=enterprise,
            score=score,
            evidence=evidence + [f"score:{score}", f"grade:{grade.value}"],
        )

    def _grade(self, score: float) -> WebsiteGrade:
        if score >= 90:
            return WebsiteGrade.A_PLUS
        if score >= 80:
            return WebsiteGrade.A
        if score >= 65:
            return WebsiteGrade.B
        if score >= 45:
            return WebsiteGrade.C
        return WebsiteGrade.F
