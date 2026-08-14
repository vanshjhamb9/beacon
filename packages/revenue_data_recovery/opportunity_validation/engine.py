from __future__ import annotations

from typing import Any

from revenue_data_recovery.models.types import AttributedValue, OpportunityValidationResult, UNKNOWN

BUYING_KEYS = ("buying", "purchase", "rfp", "budget", "vendor", "evaluating", "procurement")
TECH_KEYS = ("openai", "anthropic", "gemini", "aws", "azure", "gcp", "zendesk", "salesforce", "hubspot", "llm", "api")
BUSINESS_KEYS = ("saas", "b2b", "enterprise", "smb", "agency", "revenue", "customers")
HIRING_KEYS = ("hiring", "job", "careers", "open role", "recruiting", "headcount")
FUNDING_KEYS = ("funding", "raised", "series", "seed", "venture", "investment")
GROWTH_KEYS = ("scaling", "expansion", "growth", "new market", "international", "new office")
PAIN_KEYS = ("manual", "legacy", "support ticket", "churn", "bottleneck", "outdated", "pain")


class OpportunityValidationEngine:
    """Every opportunity must explain why Beacon collected it — else reject."""

    def validate(self, payload: dict[str, Any]) -> OpportunityValidationResult:
        source = str(payload.get("source") or UNKNOWN)
        collected_at = payload.get("collected_at") or payload.get("last_seen_at")
        corpus = self._corpus(payload)
        evidence: list[str] = []
        rejections: list[str] = []

        why = str(payload.get("why_collected") or payload.get("collection_reason") or "").strip()
        if not why:
            # Derive attributable why from source + top signal — still evidence-based
            if payload.get("evidence") or payload.get("signals") or payload.get("timeline"):
                why = f"Collected from {source} with observed opportunity evidence"
                evidence.append("why_derived_from_evidence")
            else:
                why = UNKNOWN
                rejections.append("no_collection_reason")

        buying = self._signal(corpus, BUYING_KEYS, source, collected_at, "buying_signal")
        technology = self._signal(corpus, TECH_KEYS, source, collected_at, "technology_signal")
        business = self._signal(corpus, BUSINESS_KEYS, source, collected_at, "business_signal")
        hiring = self._signal(corpus, HIRING_KEYS, source, collected_at, "hiring_signal")
        funding = self._signal(corpus, FUNDING_KEYS, source, collected_at, "funding_signal")
        growth = self._signal(corpus, GROWTH_KEYS, source, collected_at, "growth_signal")
        pain = self._signal(corpus, PAIN_KEYS, source, collected_at, "pain_point")

        signal_hits = [
            s
            for s in (buying, technology, business, hiring, funding, growth, pain)
            if s.value != UNKNOWN
        ]
        if not signal_hits:
            rejections.append("no_buying_or_business_signal")

        if not (payload.get("evidence") or payload.get("evidence_ids") or payload.get("timeline")):
            rejections.append("no_opportunity_evidence")

        recommended = payload.get("recommended_service")
        estimate = payload.get("estimated_project_value") or payload.get("estimated_value")
        # Allow empty recommendation at validation stage — recommendation engine fills later
        recommended_field = AttributedValue.of(
            recommended,
            source=source,
            collected_at=collected_at,
            confidence=70.0 if recommended else None,
            evidence=["service_observed"] if recommended else ["service_pending"],
        )
        estimate_field = AttributedValue.of(
            estimate,
            source=source,
            collected_at=collected_at,
            confidence=60.0 if estimate else None,
            evidence=["estimate_observed"] if estimate else ["estimate_pending"],
        )

        confidence = min(
            95.0,
            20.0 * len(signal_hits)
            + (15.0 if why != UNKNOWN else 0.0)
            + (10.0 if payload.get("evidence") else 0.0),
        )
        accepted = len(rejections) == 0 and why != UNKNOWN
        if accepted:
            evidence.append("opportunity:accepted")
        else:
            evidence.extend(f"reject:{r}" for r in rejections)

        return OpportunityValidationResult(
            accepted=accepted,
            why_collected=why if why != UNKNOWN else UNKNOWN,
            buying_signal=buying,
            technology_signal=technology,
            business_signal=business,
            hiring_signal=hiring,
            funding_signal=funding,
            growth_signal=growth,
            pain_point=pain,
            recommended_service=recommended_field,
            estimated_project_value=estimate_field,
            confidence=round(confidence, 2),
            rejection_reasons=rejections,
            evidence=evidence or ["validated"],
        )

    def _corpus(self, payload: dict[str, Any]) -> str:
        parts: list[str] = [
            str(payload.get("narrative") or ""),
            str(payload.get("memory_summary") or ""),
            str(payload.get("description") or ""),
            str(payload.get("use_case") or ""),
        ]
        for s in payload.get("signals") or []:
            parts.append(str(s.get("value") if isinstance(s, dict) else s))
        for row in payload.get("timeline") or []:
            if isinstance(row, dict):
                parts.append(str(row.get("signal_type") or ""))
                parts.append(str(row.get("summary") or ""))
            else:
                parts.append(str(row))
        for item in payload.get("evidence") or []:
            if isinstance(item, dict):
                parts.append(str(item.get("summary") or item.get("text") or ""))
            else:
                parts.append(str(item))
        for t in payload.get("technologies") or []:
            parts.append(str(t.get("name") if isinstance(t, dict) else t))
        return " ".join(parts).lower()

    def _signal(
        self,
        corpus: str,
        keys: tuple[str, ...],
        source: str,
        collected_at: Any,
        label: str,
    ) -> AttributedValue:
        hits = [k for k in keys if k in corpus]
        if not hits:
            return AttributedValue.unknown(reason=f"no_{label}")
        return AttributedValue.of(
            hits[0],
            source=source,
            collected_at=collected_at,
            confidence=min(95.0, 55.0 + 8.0 * len(hits)),
            evidence=[f"{label}:{h}" for h in hits],
        )
