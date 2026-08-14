from __future__ import annotations

from typing import Any

from sales_copilot.models.types import EvidenceItem, INSUFFICIENT, SalesCopilotInput


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _first(*values: Any) -> str:
    for value in values:
        text = _text(value)
        if text and text.lower() not in {"unknown", "none", "n/a"}:
            return text
    return ""


class ContextAssembler:
    """Assemble grounded facts exclusively from Beacon engine payloads."""

    def assemble(self, item: SalesCopilotInput) -> dict[str, Any]:
        evidence = self._evidence(item)
        facts = {
            "company_name": item.company_name or INSUFFICIENT,
            "domain": item.domain or _first(item.company.get("primary_domain"), item.lead_enrichment.get("company_profile", {}).get("website")),
            "website": item.website
            or _first(
                (item.lead_enrichment.get("company_profile") or {}).get("website"),
                item.company.get("primary_domain"),
            ),
            "industry": item.industry
            or _first(
                item.company.get("industry"),
                (item.lead_enrichment.get("company_profile") or {}).get("industry"),
                (item.context.get("dna") or {}).get("industry"),
            ),
            "opportunity_score": item.opportunity_score,
            "opportunity_status": item.opportunity_status or _text(item.opportunity.get("status")),
            "business_pain": item.business_pain
            or _first(
                item.revenue.get("business_pain"),
                item.lead_enrichment.get("business_pain"),
                item.opportunity_narrative,
                item.opportunity.get("narrative"),
            ),
            "recommended_service": item.recommended_service
            or _first(
                item.revenue.get("recommended_service"),
                item.lead_enrichment.get("recommended_service"),
                item.decision_makers.get("recommended_service"),
            ),
            "buyer_persona": item.buyer_persona
            or _first(
                item.revenue.get("buyer_persona"),
                item.lead_enrichment.get("buyer_persona"),
                item.decision_makers.get("buyer_persona"),
            ),
            "business_model": _first(
                (item.context.get("dna") or {}).get("business_model"),
                (item.lead_enrichment.get("company_profile") or {}).get("business_model"),
                (item.context.get("profile") or {}).get("business_model"),
            ),
            "current_situation": _first(
                item.opportunity_narrative,
                item.opportunity.get("narrative"),
                item.lead_enrichment.get("why_now"),
            ),
            "pain_points": self._list_or_fallback(
                item.context.get("pains"),
                item.revenue.get("pain_points"),
                item.lead_enrichment.get("pain_points"),
                fallback_text=item.business_pain
                or _first(item.revenue.get("business_pain"), item.lead_enrichment.get("business_pain")),
            ),
            "growth_signals": self._signals(item, kinds=("growth", "expansion", "funding", "launch")),
            "buying_signals": self._signals(item, kinds=("buying", "intent", "procurement", "evaluation")),
            "technology_stack": self._technologies(item),
            "recent_hiring": self._hiring(item),
            "decision_makers": self._decision_makers(item),
            "value_proposition": _first(
                item.revenue.get("value_proposition"),
                (item.revenue.get("playbook") or {}).get("value_proposition"),
                item.lead_enrichment.get("why_now"),
            ),
            "conversation_angles": self._list_or_fallback(
                item.revenue.get("conversation_angles"),
                (item.revenue.get("playbook") or {}).get("conversation_angles"),
                item.lead_enrichment.get("outreach_angles"),
            ),
            "timeline_highlights": self._timeline(item),
            "verification_status": _first(
                item.verification.get("decision"),
                (item.verification.get("trust") or {}).get("status"),
            ),
            "quality_decision": _first(item.quality.get("decision"), item.quality.get("status")),
        }
        facts["evidence"] = evidence
        facts["evidence_index"] = {item.reference_id or f"ev-{idx}": item for idx, item in enumerate(evidence)}
        return facts

    def _evidence(self, item: SalesCopilotInput) -> list[EvidenceItem]:
        chain: list[EvidenceItem] = []
        seen: set[str] = set()

        def add(category: str, summary: str, source: str, *, confidence: float = 70.0, reference_id: str | None = None, source_url: str | None = None) -> None:
            summary = _text(summary)
            if not summary:
                return
            key = f"{category}:{summary}:{reference_id or ''}"
            if key in seen:
                return
            seen.add(key)
            chain.append(
                EvidenceItem(
                    category=category,
                    summary=summary,
                    source=source,
                    source_url=source_url,
                    confidence=max(0.0, min(100.0, confidence)),
                    reference_id=reference_id,
                )
            )

        add("opportunity", f"Opportunity score {item.opportunity_score:.1f}", "beacon_opportunity", confidence=min(100.0, item.opportunity_score), reference_id=str(item.opportunity_id))
        if item.business_pain or item.revenue.get("business_pain"):
            add("pain", item.business_pain or str(item.revenue.get("business_pain")), "beacon_revenue", reference_id=f"pain-{item.opportunity_id}")
        if item.recommended_service or item.revenue.get("recommended_service"):
            add(
                "service",
                f"Recommended service: {item.recommended_service or item.revenue.get('recommended_service')}",
                "beacon_revenue",
                reference_id=f"service-{item.opportunity_id}",
            )
        for row in item.evidence_chain:
            add(
                _text(row.get("category")) or "evidence",
                _text(row.get("summary")) or _text(row.get("explanation")),
                _text(row.get("source")) or "beacon_context",
                confidence=float(row.get("confidence") or 60.0),
                reference_id=_text(row.get("reference_id")) or None,
                source_url=_text(row.get("source_url")) or None,
            )
        for pain in item.context.get("pains") or []:
            if isinstance(pain, dict):
                add("pain", _text(pain.get("description") or pain.get("title")), "beacon_context", confidence=float(pain.get("confidence") or 65.0), reference_id=_text(pain.get("id")) or None)
            else:
                add("pain", _text(pain), "beacon_context")
        for tech in (item.lead_enrichment.get("technologies") or item.lead_enrichment.get("technology_stack") or []):
            if isinstance(tech, dict):
                add("technology", _text(tech.get("name") or tech.get("technology")), "beacon_enrichment", confidence=float(tech.get("confidence") or 70.0), reference_id=_text(tech.get("id")) or None, source_url=_text(tech.get("source_url")) or None)
            else:
                add("technology", _text(tech), "beacon_enrichment")
        for job in item.lead_enrichment.get("jobs") or item.lead_enrichment.get("recent_hiring") or []:
            if isinstance(job, dict):
                add("hiring", _text(job.get("title") or job.get("role")), "beacon_enrichment", confidence=float(job.get("confidence") or 70.0))
            else:
                add("hiring", _text(job), "beacon_enrichment")
        makers = item.decision_makers.get("decision_makers") or []
        primary = item.decision_makers.get("primary_decision_maker")
        if primary:
            makers = [primary, *makers]
        for maker in makers:
            if not isinstance(maker, dict):
                continue
            name = _first(maker.get("name"))
            role = _first(maker.get("role"), maker.get("normalized_role"))
            if name:
                add("decision_maker", f"{name} — {role or 'role unknown'}", "beacon_decision", confidence=float(maker.get("confidence") or 70.0), reference_id=_text(maker.get("id")) or None, source_url=_text(maker.get("source_url")) or None)
        for event in item.timeline[:12]:
            add(
                "timeline",
                _first(event.get("summary"), event.get("title"), event.get("event_type")),
                "beacon_intelligence",
                confidence=float(event.get("confidence") or 60.0),
                reference_id=_text(event.get("id")) or None,
            )
        for node in (item.knowledge_graph.get("nodes") or [])[:20]:
            if isinstance(node, dict):
                add("knowledge_graph", _first(node.get("label"), node.get("name"), node.get("node_type")), "beacon_intelligence", reference_id=_text(node.get("id")) or None)
        if item.verification:
            add(
                "verification",
                f"Verification decision: {_first(item.verification.get('decision'), 'reviewed')}",
                "beacon_verification",
                confidence=float((item.verification.get("trust") or {}).get("score") or item.verification.get("overall_score") or 70.0),
                reference_id=_text(item.verification.get("id")) or None,
            )
        return chain

    def _list_or_fallback(self, *candidates: Any, fallback_text: str = "") -> list[str]:
        values: list[str] = []
        for candidate in candidates:
            if not candidate:
                continue
            if isinstance(candidate, list):
                for row in candidate:
                    if isinstance(row, dict):
                        text = _first(row.get("description"), row.get("title"), row.get("summary"), row.get("angle"), row.get("text"))
                    else:
                        text = _text(row)
                    if text and text not in values:
                        values.append(text)
            elif isinstance(candidate, str) and candidate.strip():
                values.append(candidate.strip())
        if values:
            return values
        if fallback_text:
            return [fallback_text]
        return []

    def _signals(self, item: SalesCopilotInput, *, kinds: tuple[str, ...]) -> list[str]:
        rows: list[str] = []
        for event in item.timeline:
            blob = " ".join(
                _text(event.get(key)) for key in ("event_type", "summary", "title", "category")
            ).lower()
            if any(kind in blob for kind in kinds):
                text = _first(event.get("summary"), event.get("title"), event.get("event_type"))
                if text and text not in rows:
                    rows.append(text)
        for signal in item.opportunity.get("signals") or item.lead_enrichment.get("signals") or []:
            if isinstance(signal, dict):
                text = _first(signal.get("summary"), signal.get("title"), signal.get("type"))
            else:
                text = _text(signal)
            if text and text not in rows:
                rows.append(text)
        return rows

    def _technologies(self, item: SalesCopilotInput) -> list[str]:
        rows: list[str] = []
        for tech in item.lead_enrichment.get("technologies") or item.lead_enrichment.get("technology_stack") or []:
            if isinstance(tech, dict):
                text = _first(tech.get("name"), tech.get("technology"))
            else:
                text = _text(tech)
            if text and text not in rows:
                rows.append(text)
        for signal in item.context.get("technologies") or []:
            if isinstance(signal, dict):
                text = _first(signal.get("name"), signal.get("technology"))
            else:
                text = _text(signal)
            if text and text not in rows:
                rows.append(text)
        return rows

    def _hiring(self, item: SalesCopilotInput) -> list[str]:
        rows: list[str] = []
        for job in item.lead_enrichment.get("jobs") or item.lead_enrichment.get("recent_hiring") or []:
            if isinstance(job, dict):
                text = _first(job.get("title"), job.get("role"))
            else:
                text = _text(job)
            if text and text not in rows:
                rows.append(text)
        hiring_pattern = _first((item.context.get("dna") or {}).get("hiring_pattern"), item.context.get("hiring_pattern"))
        if hiring_pattern:
            rows.append(hiring_pattern)
        return rows

    def _decision_makers(self, item: SalesCopilotInput) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        makers = list(item.decision_makers.get("decision_makers") or [])
        primary = item.decision_makers.get("primary_decision_maker")
        secondary = item.decision_makers.get("secondary_decision_maker")
        ordered = [primary, secondary, *makers]
        seen: set[str] = set()
        for maker in ordered:
            if not isinstance(maker, dict):
                continue
            name = _first(maker.get("name"))
            if not name or name in seen:
                continue
            seen.add(name)
            rows.append(
                {
                    "name": name,
                    "role": _first(maker.get("role"), maker.get("normalized_role")) or "Unknown role",
                    "evidence": _first(maker.get("evidence"), maker.get("source")) or "beacon_decision",
                }
            )
        return rows

    def _timeline(self, item: SalesCopilotInput) -> list[str]:
        rows: list[str] = []
        for event in item.timeline[:8]:
            text = _first(event.get("summary"), event.get("title"), event.get("event_type"))
            if text and text not in rows:
                rows.append(text)
        return rows
