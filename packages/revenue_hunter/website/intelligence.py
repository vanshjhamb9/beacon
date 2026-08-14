from __future__ import annotations

from typing import Any

from revenue_hunter.models.types import RevenueHunterInput, WebsiteIntelligence, WebsiteOpportunity


class WebsiteIntelligenceEngine:
    """Analyze homepage/speed/CWV/SEO/a11y/stack and emit improvement opportunities."""

    def analyze(self, item: RevenueHunterInput) -> WebsiteIntelligence:
        metrics = dict(item.website_metrics or {})
        tech = list(item.technologies)

        lcp = self._float(metrics.get("lcp_ms") or metrics.get("lcp"))
        cls = self._float(metrics.get("cls"))
        inp = self._float(metrics.get("inp_ms") or metrics.get("inp"))
        speed = self._float(metrics.get("speed_score") or metrics.get("performance"))
        seo = self._float(metrics.get("seo_score") or metrics.get("seo"))
        a11y = self._float(metrics.get("accessibility_score") or metrics.get("accessibility"))
        homepage = self._float(metrics.get("homepage_score") or metrics.get("overall"))

        if speed is None:
            speed = self._speed_from_cwv(lcp, cls, inp)
        if seo is None:
            seo = 55.0 if any(t.lower() in {"wordpress", "webflow", "shopify"} for t in tech) else 45.0
        if a11y is None:
            a11y = float(metrics.get("a11y", 50.0))
        if homepage is None:
            homepage = round((speed + seo + a11y) / 3.0, 4)

        cms = self._detect_cms(tech, metrics)
        analytics = self._detect_list(tech, metrics, "analytics", ["google analytics", "ga4", "mixpanel", "amplitude", "segment"])
        pixels = self._detect_list(tech, metrics, "pixels", ["facebook pixel", "meta pixel", "linkedin insight", "tiktok pixel"])
        has_forms = bool(metrics.get("has_forms")) or any("form" in t.lower() for t in tech)
        has_chatbot = bool(metrics.get("has_chatbot")) or any(
            t.lower() in {"intercom", "drift", "zendesk chat", "crisp", "tawk"} for t in tech
        )
        broken = [str(p) for p in (metrics.get("broken_pages") or [])]

        opportunities = self._opportunities(
            speed=speed,
            seo=seo,
            a11y=a11y,
            lcp=lcp,
            cls=cls,
            has_forms=has_forms,
            has_chatbot=has_chatbot,
            broken=broken,
            cms=cms,
        )
        evidence = [
            f"homepage_score:{homepage}",
            f"speed_score:{speed}",
            f"seo_score:{seo}",
            f"accessibility_score:{a11y}",
        ]
        if lcp is not None:
            evidence.append(f"lcp_ms:{lcp}")
        if cms:
            evidence.append(f"cms:{cms}")
        if broken:
            evidence.append(f"broken_pages:{len(broken)}")

        return WebsiteIntelligence(
            homepage_score=round(homepage, 4),
            speed_score=round(speed, 4),
            seo_score=round(seo, 4),
            accessibility_score=round(a11y, 4),
            lcp_ms=lcp,
            cls=cls,
            inp_ms=inp,
            cms=cms,
            analytics=analytics,
            pixels=pixels,
            has_forms=has_forms,
            has_chatbot=has_chatbot,
            broken_pages=broken,
            technology_stack=tech,
            opportunities=opportunities,
            evidence=evidence,
        )

    def _opportunities(
        self,
        *,
        speed: float,
        seo: float,
        a11y: float,
        lcp: float | None,
        cls: float | None,
        has_forms: bool,
        has_chatbot: bool,
        broken: list[str],
        cms: str | None,
    ) -> list[WebsiteOpportunity]:
        ops: list[WebsiteOpportunity] = []
        if speed < 60 or (lcp is not None and lcp > 2500):
            ops.append(
                WebsiteOpportunity(
                    area="speed",
                    recommendation="Improve Core Web Vitals and page speed — LCP/INP likely costing conversions.",
                    severity="high",
                    evidence=[f"speed_score:{speed}"] + ([f"lcp_ms:{lcp}"] if lcp is not None else []),
                )
            )
        if seo < 55:
            ops.append(
                WebsiteOpportunity(
                    area="seo",
                    recommendation="Fix SEO basics: titles, meta, headings, sitemap, and indexation.",
                    severity="medium",
                    evidence=[f"seo_score:{seo}"],
                )
            )
        if a11y < 60:
            ops.append(
                WebsiteOpportunity(
                    area="accessibility",
                    recommendation="Raise accessibility: contrast, labels, keyboard nav, alt text.",
                    severity="medium",
                    evidence=[f"accessibility_score:{a11y}"],
                )
            )
        if cls is not None and cls > 0.1:
            ops.append(
                WebsiteOpportunity(
                    area="stability",
                    recommendation="Reduce layout shift (CLS) on hero and above-the-fold content.",
                    severity="medium",
                    evidence=[f"cls:{cls}"],
                )
            )
        if broken:
            ops.append(
                WebsiteOpportunity(
                    area="reliability",
                    recommendation=f"Repair {len(broken)} broken page(s) hurting trust and crawl health.",
                    severity="high",
                    evidence=broken[:5],
                )
            )
        if not has_forms:
            ops.append(
                WebsiteOpportunity(
                    area="conversion",
                    recommendation="Add clear lead-capture forms or CTA paths on homepage.",
                    severity="high",
                    evidence=["missing_forms"],
                )
            )
        if not has_chatbot:
            ops.append(
                WebsiteOpportunity(
                    area="engagement",
                    recommendation="Add AI chatbot / conversational capture for inbound intent.",
                    severity="low",
                    evidence=["missing_chatbot"],
                )
            )
        if cms and cms.lower() in {"wordpress", "wix", "squarespace"}:
            ops.append(
                WebsiteOpportunity(
                    area="modernization",
                    recommendation=f"Evaluate modern rebuild vs {cms} — performance and maintainability risks.",
                    severity="low",
                    evidence=[f"cms:{cms}"],
                )
            )
        return ops

    def _speed_from_cwv(self, lcp: float | None, cls: float | None, inp: float | None) -> float:
        score = 70.0
        if lcp is not None:
            if lcp > 4000:
                score -= 35
            elif lcp > 2500:
                score -= 20
            elif lcp > 1800:
                score -= 8
        if cls is not None:
            if cls > 0.25:
                score -= 20
            elif cls > 0.1:
                score -= 10
        if inp is not None:
            if inp > 500:
                score -= 15
            elif inp > 200:
                score -= 8
        return max(5.0, min(100.0, score))

    def _detect_cms(self, tech: list[str], metrics: dict[str, Any]) -> str | None:
        if metrics.get("cms"):
            return str(metrics["cms"])
        known = {
            "wordpress": "WordPress",
            "webflow": "Webflow",
            "shopify": "Shopify",
            "wix": "Wix",
            "squarespace": "Squarespace",
            "next.js": "Next.js",
            "nextjs": "Next.js",
            "drupal": "Drupal",
        }
        for t in tech:
            key = t.lower()
            for needle, label in known.items():
                if needle in key:
                    return label
        return None

    def _detect_list(
        self,
        tech: list[str],
        metrics: dict[str, Any],
        key: str,
        needles: list[str],
    ) -> list[str]:
        raw = metrics.get(key)
        if isinstance(raw, list) and raw:
            return [str(x) for x in raw]
        found: list[str] = []
        blob = " ".join(tech).lower()
        for n in needles:
            if n in blob:
                found.append(n)
        return found

    def _float(self, value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
