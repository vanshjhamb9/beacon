from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from founder_os.models.types import FounderOsInput, MeetingIntelligencePack


DISCOVERY_QUESTIONS = [
    "What broke in the last 90 days that made this a priority now?",
    "Who owns the budget and the technical decision?",
    "What does success look like in 30 / 60 / 90 days?",
    "Which tools are already in place that we must integrate with?",
    "What happens if you do nothing for another quarter?",
]

OBJECTIONS = [
    "We already have an internal team",
    "Budget is locked this quarter",
    "We tried an agency before",
    "Need security / compliance review first",
]


class MeetingIntelligenceEngine:
    def generate(self, data: FounderOsInput) -> list[MeetingIntelligencePack]:
        packs: list[MeetingIntelligencePack] = []
        for row in data.meetings:
            company_id = self._uuid(row.get("company_id"))
            if company_id is None:
                continue
            name = str(row.get("company_name") or "Unknown")
            service = str(row.get("recommended_service") or "Custom AI")
            pains = [str(p) for p in (row.get("pain_points") or row.get("pains") or [])][:6]
            signals = [str(s) for s in (row.get("buying_signals") or row.get("signals") or [])][:8]
            problems = [str(p) for p in (row.get("business_problems") or pains)][:6]
            dms = list(row.get("decision_makers") or [])
            summary = str(
                row.get("company_summary")
                or f"{name} — pitch {service}; grade {row.get('priority_grade', 'n/a')}."
            )
            packs.append(
                MeetingIntelligencePack(
                    company_id=company_id,
                    company_name=name,
                    scheduled_at=self._dt(row.get("scheduled_at")),
                    company_summary=summary,
                    decision_makers=dms,
                    business_problems=problems or ["Operational friction requiring scoped delivery"],
                    pain_points=pains,
                    buying_signals=signals,
                    timeline_summary=str(row.get("timeline_summary") or row.get("expected_timeline") or "6–10 weeks"),
                    discovery_questions=list(DISCOVERY_QUESTIONS),
                    possible_objections=list(OBJECTIONS),
                    suggested_demo=str(
                        row.get("suggested_demo")
                        or f"15-min live walkthrough of {service} solving their top pain."
                    ),
                    closing_strategy=str(
                        row.get("closing_strategy")
                        or "Confirm pain owner → quantify cost of status quo → propose paid discovery workshop."
                    ),
                    meeting_notes=str(row.get("meeting_notes") or ""),
                    next_actions=[
                        "Send agenda 2 hours before",
                        "Confirm decision-maker attendance",
                        "Prepare one relevant case study",
                        "Agree next step before leave",
                    ],
                    evidence=[
                        f"service:{service}",
                        f"pains:{len(pains)}",
                        f"signals:{len(signals)}",
                        f"dms:{len(dms)}",
                    ],
                )
            )
        return packs

    def _uuid(self, value: object) -> UUID | None:
        if value is None:
            return None
        try:
            return value if isinstance(value, UUID) else UUID(str(value))
        except (TypeError, ValueError):
            return None

    def _dt(self, value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
