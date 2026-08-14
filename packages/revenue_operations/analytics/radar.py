from __future__ import annotations

from revenue_operations.models.types import OpportunitySignal, RadarSignal, RadarSignalKind, RevenueOperationsInput

HINT_MAP: list[tuple[list[str], RadarSignalKind, float]] = [
    (["funding", "raised", "series", "seed"], RadarSignalKind.FUNDING, 18.0),
    (["hiring ai", "ai engineer"], RadarSignalKind.HIRING_AI_ENGINEERS, 14.0),
    (["hiring software", "software developer"], RadarSignalKind.HIRING_SOFTWARE_DEVELOPERS, 10.0),
    (["hiring product", "product manager"], RadarSignalKind.HIRING_PRODUCT_MANAGERS, 10.0),
    (["hiring automation", "automation engineer"], RadarSignalKind.HIRING_AUTOMATION_ENGINEERS, 12.0),
    (["hiring", "open roles", "we're hiring"], RadarSignalKind.HIRING, 8.0),
    (["product launch", "launched", "new product"], RadarSignalKind.PRODUCT_LAUNCH, 12.0),
    (["ai adoption", "adopting ai", "chatgpt", "llm"], RadarSignalKind.AI_ADOPTION, 15.0),
    (["cloud migration", "migrate to aws", "azure", "gcp"], RadarSignalKind.CLOUD_MIGRATION, 11.0),
    (["digital transformation", "digitize", "modernize"], RadarSignalKind.DIGITAL_TRANSFORMATION, 10.0),
    (["new office", "opened office"], RadarSignalKind.NEW_OFFICE, 9.0),
    (["expansion", "expanding", "new market"], RadarSignalKind.EXPANSION, 10.0),
    (["ceo", "cto", "cfo", "leadership", "appointed"], RadarSignalKind.LEADERSHIP_CHANGE, 13.0),
    (["decision maker", "new vp", "head of"], RadarSignalKind.DECISION_MAKER_CHANGE, 12.0),
    (["website redesign", "rebrand", "new site"], RadarSignalKind.WEBSITE_REDESIGN, 7.0),
    (["stack", "migrated to", "switched to", "technology"], RadarSignalKind.TECHNOLOGY_CHANGE, 9.0),
    (["tech stack", "adopted"], RadarSignalKind.TECH_STACK_CHANGE, 9.0),
]


class RevenueRadarEngine:
    """Continuously classify buying signals and hunter score deltas."""

    def scan(self, item: RevenueOperationsInput) -> list[RadarSignal]:
        signals: list[RadarSignal] = []
        for opp in item.opportunities:
            signals.extend(self._scan_opportunity(opp))
        signals.sort(key=lambda s: (-s.intensity, s.company_name, s.kind.value))
        return signals

    def _scan_opportunity(self, opp: OpportunitySignal) -> list[RadarSignal]:
        blob = " ".join(opp.radar_hints + opp.technologies + [opp.stage or "", opp.service or ""]).lower()
        out: list[RadarSignal] = []
        seen: set[RadarSignalKind] = set()
        for patterns, kind, delta in HINT_MAP:
            if kind in seen:
                continue
            hits = [p for p in patterns if p in blob]
            if not hits:
                continue
            seen.add(kind)
            intensity = min(100.0, 40.0 + 10.0 * len(hits) + (opp.probability / 5.0))
            out.append(
                RadarSignal(
                    kind=kind,
                    company_id=opp.company_id,
                    company_name=opp.company_name,
                    detail=f"Detected {kind.value.replace('_', ' ')} for {opp.company_name}",
                    intensity=round(intensity, 2),
                    hunter_score_delta=delta,
                    evidence=[f"hits:{','.join(hits[:3])}", f"company:{opp.company_name}"],
                )
            )
        return out

    def hunter_score_updates(self, signals: list[RadarSignal]) -> dict[str, float]:
        updates: dict[str, float] = {}
        for s in signals:
            key = str(s.company_id or s.company_name)
            updates[key] = updates.get(key, 0.0) + s.hunter_score_delta
        return updates
