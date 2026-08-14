from __future__ import annotations

from autonomous_sales_agent.models.types import AutonomousSalesAgentInput, ObjectionKind, ObjectionRecord


OBJECTION_MAP: list[tuple[ObjectionKind, list[str]]] = [
    (ObjectionKind.BUDGET, ["budget", "expensive", "cost", "price"]),
    (ObjectionKind.TIMING, ["timing", "later", "next quarter", "busy"]),
    (ObjectionKind.NO_TEAM, ["no team", "bandwidth", "understaffed"]),
    (ObjectionKind.EXISTING_VENDOR, ["vendor", "already use", "incumbent"]),
    (ObjectionKind.NEED_APPROVAL, ["approval", "board", "committee"]),
    (ObjectionKind.NO_URGENCY, ["no urgency", "not priority", "someday"]),
    (ObjectionKind.NOT_INTERESTED, ["not interested", "pass", "no thanks"]),
    (ObjectionKind.WRONG_CONTACT, ["wrong person", "not the right", "forward"]),
    (ObjectionKind.NEED_PROPOSAL, ["proposal", "quote", "sow"]),
    (ObjectionKind.NEED_DEMO, ["demo", "show me", "walkthrough"]),
]


class ObjectionTrackerEngine:
    def track(self, item: AutonomousSalesAgentInput) -> list[ObjectionRecord]:
        blob = " ".join(item.objections_seen + item.recent_activity + item.pains).lower()
        out: list[ObjectionRecord] = []
        for kind, patterns in OBJECTION_MAP:
            hits = [p for p in patterns if p in blob]
            if not hits and kind.value not in item.objections_seen:
                continue
            freq = max(1, len(hits) or (1 if kind.value in item.objections_seen else 0))
            # Deterministic pseudo win-rate from memory signals without mutating engines
            base = float((item.memory_signals or {}).get("objection_win_rates", {}).get(kind.value, 35.0))
            win_rate = min(80.0, base + (5.0 if item.priority_grade in {"A+", "A"} else 0.0))
            out.append(
                ObjectionRecord(
                    objection=kind,
                    frequency=freq,
                    industry=item.industry,
                    company_size=item.company_size,
                    win_rate=round(win_rate, 4),
                    evidence=[f"hits:{','.join(hits[:4])}" if hits else f"listed:{kind.value}"],
                )
            )
        out.sort(key=lambda r: (-r.frequency, r.objection.value))
        return out
