from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.intelligence import Company
from app.models.operation_first_customer import (
    OfcDailyReport,
    OfcFounderNote,
    OfcObjectionEvent,
    OfcOutreachRecord,
    OfcTimelineEvent,
)
from operation_first_customer.analytics.engine import OfcAnalyticsEngine
from operation_first_customer.briefs.engine import OutreachBriefEngine
from operation_first_customer.daily_action.engine import DailyActionEngine
from operation_first_customer.models.types import (
    ALLOWED_TRANSITIONS,
    DEFAULT_PIPELINE_VALUE,
    VERSION,
    ObjectionLabel,
    OutreachStatus,
    TimelineEventType,
)


class OperationFirstCustomerService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.briefs = OutreachBriefEngine()
        self.analytics = OfcAnalyticsEngine()
        self.daily = DailyActionEngine()

    async def sync_from_revenue_ready(self) -> dict[str, Any]:
        """Create/refresh Outreach Records for every Revenue Ready company. No new companies."""
        companies = (
            await self.session.execute(select(Company).where(Company.deleted_at.is_(None)))
        ).scalars().all()
        rr = [
            c
            for c in companies
            if (c.attributes or {}).get("rrp_revenue_ready") or (c.attributes or {}).get("rdap_revenue_ready")
        ]
        existing = (
            await self.session.execute(
                select(OfcOutreachRecord).where(OfcOutreachRecord.deleted_at.is_(None))
            )
        ).scalars().all()
        by_company = {r.company_id: r for r in existing}
        created = 0
        refreshed = 0
        now = datetime.now(UTC).isoformat()

        for company in rr:
            brief = self.briefs.build(
                {
                    "id": str(company.id),
                    "name": company.name,
                    "primary_domain": company.primary_domain,
                    "attributes": company.attributes or {},
                }
            ).model_dump(mode="json")
            value = self._pipeline_value(brief)
            if company.id in by_company:
                rec = by_company[company.id]
                rec.brief = brief
                rec.company_name = company.name
                rec.pipeline_value = value
                rec.payload = {**(rec.payload or {}), "refreshed_at": now}
                flag_modified(rec, "brief")
                flag_modified(rec, "payload")
                refreshed += 1
            else:
                hist = [{"status": OutreachStatus.READY, "at": now, "note": "Synced from Revenue Ready"}]
                rec = OfcOutreachRecord(
                    id=uuid.uuid4(),
                    company_id=company.id,
                    company_name=company.name,
                    status=OutreachStatus.READY,
                    status_history=hist,
                    brief=brief,
                    pipeline_value=value,
                    payload={"synced_at": now},
                    scoring_version=VERSION,
                )
                self.session.add(rec)
                self.session.add(
                    OfcTimelineEvent(
                        id=uuid.uuid4(),
                        record_id=rec.id,
                        company_id=company.id,
                        event_type=TimelineEventType.STATUS_CHANGE,
                        payload={"to": OutreachStatus.READY, "at": now, "source": "sync"},
                    )
                )
                created += 1

        await self.session.flush()
        report = await self.build_report()
        return {"created": created, "refreshed": refreshed, "revenue_ready": len(rr), "report": report}

    async def list_records(self) -> dict[str, Any]:
        records = await self._record_dicts()
        action = self.daily.decide(records)
        return {
            "items": records,
            "count": len(records),
            "today_action": action.model_dump(mode="json"),
            "scoring_version": VERSION,
        }

    async def get_record(self, record_id: UUID) -> dict[str, Any]:
        rec = await self._get_record(record_id)
        if not rec:
            return {"status": "not_found"}
        timeline = await self._timeline(rec.id)
        notes = await self._notes(rec.id)
        objections = await self._objections_for_record(rec.id)
        return {
            "record": self._to_dict(rec),
            "timeline": timeline,
            "notes": notes,
            "objections": objections,
        }

    async def transition(self, record_id: UUID, to_status: str, *, note: str | None = None) -> dict[str, Any]:
        rec = await self._get_record(record_id)
        if not rec:
            return {"status": "not_found"}
        try:
            target = OutreachStatus(to_status)
            current = OutreachStatus(rec.status)
        except ValueError:
            return {"status": "invalid_status", "allowed": [s.value for s in OutreachStatus]}
        allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
        if target not in allowed and target != current:
            return {
                "status": "transition_denied",
                "from": current.value,
                "to": target.value,
                "allowed": sorted(s.value for s in allowed),
            }
        now = datetime.now(UTC).isoformat()
        hist = list(rec.status_history or [])
        hist.append({"status": target.value, "at": now, "note": note})
        rec.status = target.value
        rec.status_history = hist
        flag_modified(rec, "status_history")

        event_type = TimelineEventType.STATUS_CHANGE
        if target == OutreachStatus.CONTACTED:
            event_type = TimelineEventType.EMAIL_SENT
        elif target == OutreachStatus.REPLIED:
            event_type = TimelineEventType.REPLY_RECEIVED
        elif target == OutreachStatus.MEETING_BOOKED:
            event_type = TimelineEventType.MEETING_BOOKED
        elif target == OutreachStatus.PROPOSAL_SENT:
            event_type = TimelineEventType.PROPOSAL
        elif target == OutreachStatus.WON:
            event_type = TimelineEventType.WON
        elif target == OutreachStatus.LOST:
            event_type = TimelineEventType.LOST

        self.session.add(
            OfcTimelineEvent(
                id=uuid.uuid4(),
                record_id=rec.id,
                company_id=rec.company_id,
                event_type=event_type,
                payload={"from": current.value, "to": target.value, "at": now, "note": note},
            )
        )
        await self.session.flush()
        return {"status": "ok", "record": self._to_dict(rec)}

    async def add_timeline(
        self,
        record_id: UUID,
        event_type: str,
        *,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        rec = await self._get_record(record_id)
        if not rec:
            return {"status": "not_found"}
        try:
            et = TimelineEventType(event_type)
        except ValueError:
            return {"status": "invalid_event", "allowed": [e.value for e in TimelineEventType]}
        now = datetime.now(UTC).isoformat()
        body = {**(payload or {}), "at": now}
        self.session.add(
            OfcTimelineEvent(
                id=uuid.uuid4(),
                record_id=rec.id,
                company_id=rec.company_id,
                event_type=et.value,
                payload=body,
            )
        )
        # Soft-align status for key timeline events (manual founder control still via transition)
        if et == TimelineEventType.FOLLOW_UP and rec.status == OutreachStatus.CONTACTED:
            pass
        await self.session.flush()
        return {"status": "ok", "timeline": await self._timeline(rec.id)}

    async def add_note(self, record_id: UUID, note: str) -> dict[str, Any]:
        rec = await self._get_record(record_id)
        if not rec:
            return {"status": "not_found"}
        text = (note or "").strip()
        if not text:
            return {"status": "empty_note"}
        now = datetime.now(UTC).isoformat()
        self.session.add(
            OfcFounderNote(
                id=uuid.uuid4(),
                record_id=rec.id,
                company_id=rec.company_id,
                note=text[:4000],
                payload={"recorded_at": now},
            )
        )
        self.session.add(
            OfcTimelineEvent(
                id=uuid.uuid4(),
                record_id=rec.id,
                company_id=rec.company_id,
                event_type=TimelineEventType.NOTE,
                payload={"note": text[:500], "at": now},
            )
        )
        await self.session.flush()
        return {"status": "ok", "notes": await self._notes(rec.id)}

    async def add_objection(self, record_id: UUID, label: str) -> dict[str, Any]:
        rec = await self._get_record(record_id)
        if not rec:
            return {"status": "not_found"}
        try:
            obj = ObjectionLabel(label)
        except ValueError:
            return {"status": "invalid_label", "allowed": [x.value for x in ObjectionLabel]}
        now = datetime.now(UTC).isoformat()
        self.session.add(
            OfcObjectionEvent(
                id=uuid.uuid4(),
                record_id=rec.id,
                company_id=rec.company_id,
                label=obj.value,
                payload={"recorded_at": now},
            )
        )
        await self.session.flush()
        return {"status": "recorded", "label": obj.value}

    async def revenue_dashboard(self) -> dict[str, Any]:
        records = await self._record_dicts()
        funnel = self.analytics.funnel(records)
        rates = self.analytics.conversion_rates(funnel)
        action = self.daily.decide(records)
        return {
            "scoring_version": VERSION,
            "funnel": funnel,
            "conversion_rates": rates,
            "pipeline_value": self.analytics.pipeline_value(records),
            "today_action": action.model_dump(mode="json"),
            "records": records,
            "vansh_can_act_today": bool(action.company_id or action.action),
        }

    async def learning_dashboard(self) -> dict[str, Any]:
        records = await self._record_dicts()
        objections = await self._all_objections()
        learning = self.analytics.learning(records, objections)
        return {
            "scoring_version": VERSION,
            "learning": learning,
            "note": "Analytics only. Never auto-changes scoring or readiness rules.",
        }

    async def build_report(self) -> dict[str, Any]:
        records = await self._record_dicts()
        objections = await self._all_objections()
        funnel = self.analytics.funnel(records)
        rates = self.analytics.conversion_rates(funnel)
        learning = self.analytics.learning(records, objections)
        action = self.daily.decide(records)

        def n(name: str) -> int:
            return next((int(x["count"]) for x in funnel if x["name"] == name), 0)

        top_industry = (learning.get("best_industries") or [{"label": "unknown"}])[0]["label"]
        top_service = (learning.get("best_services") or [{"label": "unknown"}])[0]["label"]
        top_role = (learning.get("best_decision_maker_roles") or [{"label": "unknown"}])[0]["label"]

        report = {
            "mission": "Sprint 34 — Operation First Customer (OFC v2)",
            "generated_at": datetime.now(UTC).isoformat(),
            "scoring_version": VERSION,
            "revenue_ready_companies": n("Revenue Ready"),
            "contacted": n("Contacted"),
            "replies": n("Replies"),
            "meetings": n("Meetings"),
            "proposals": n("Proposals"),
            "won": n("Won"),
            "lost": n("Lost"),
            "pipeline_value": self.analytics.pipeline_value(records),
            "meeting_rate": rates.get("meeting_rate"),
            "reply_rate": rates.get("reply_rate"),
            "win_rate": rates.get("win_rate"),
            "average_sales_cycle_days": self.analytics.average_sales_cycle_days(records),
            "most_successful_industry": top_industry,
            "most_successful_service": top_service,
            "most_successful_decision_maker_role": top_role,
            "top_objections": learning.get("worst_rejection_reasons") or [],
            "conversion_rates": rates,
            "funnel": funnel,
            "learning": learning,
            "today_action": action.model_dump(mode="json"),
            "vansh_morning_question": {
                "question": "What should Vansh do today to close the next customer?",
                "answer": action.action,
                "why": action.why,
                "company": action.company,
                "channel": action.channel,
            },
            "can_answer_morning_question": True,
        }

        self.session.add(
            OfcDailyReport(
                id=uuid.uuid4(),
                payload=report,
                today_action=action.action,
                vansh_ready_answer="YES" if action.company or n("Revenue Ready") > 0 else "NO",
                scoring_version=VERSION,
            )
        )
        await self.session.flush()
        return report

    async def _get_record(self, record_id: UUID) -> OfcOutreachRecord | None:
        return (
            await self.session.execute(
                select(OfcOutreachRecord).where(
                    OfcOutreachRecord.id == record_id,
                    OfcOutreachRecord.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()

    async def _record_dicts(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(OfcOutreachRecord)
                .where(OfcOutreachRecord.deleted_at.is_(None))
                .order_by(OfcOutreachRecord.updated_at.desc())
            )
        ).scalars().all()
        return [self._to_dict(r) for r in rows]

    def _to_dict(self, rec: OfcOutreachRecord) -> dict[str, Any]:
        return {
            "id": str(rec.id),
            "company_id": str(rec.company_id),
            "company": rec.company_name,
            "status": rec.status,
            "status_history": list(rec.status_history or []),
            "brief": dict(rec.brief or {}),
            "pipeline_value": float(rec.pipeline_value or DEFAULT_PIPELINE_VALUE),
            "scoring_version": rec.scoring_version,
            "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
        }

    async def _timeline(self, record_id: UUID) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(OfcTimelineEvent)
                .where(
                    OfcTimelineEvent.record_id == record_id,
                    OfcTimelineEvent.deleted_at.is_(None),
                )
                .order_by(OfcTimelineEvent.created_at.asc())
            )
        ).scalars().all()
        return [
            {
                "id": str(r.id),
                "event_type": r.event_type,
                "payload": r.payload,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    async def _notes(self, record_id: UUID) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(OfcFounderNote)
                .where(
                    OfcFounderNote.record_id == record_id,
                    OfcFounderNote.deleted_at.is_(None),
                )
                .order_by(OfcFounderNote.created_at.desc())
            )
        ).scalars().all()
        return [
            {
                "id": str(r.id),
                "note": r.note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]

    async def _objections_for_record(self, record_id: UUID) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(OfcObjectionEvent)
                .where(
                    OfcObjectionEvent.record_id == record_id,
                    OfcObjectionEvent.deleted_at.is_(None),
                )
                .order_by(OfcObjectionEvent.created_at.desc())
            )
        ).scalars().all()
        return [{"id": str(r.id), "label": r.label, "created_at": r.created_at.isoformat() if r.created_at else None} for r in rows]

    async def _all_objections(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(OfcObjectionEvent).where(OfcObjectionEvent.deleted_at.is_(None))
            )
        ).scalars().all()
        return [{"label": r.label, "record_id": str(r.record_id)} for r in rows]

    def _pipeline_value(self, brief: dict[str, Any]) -> float:
        service = str(brief.get("recommended_service") or "")
        base = DEFAULT_PIPELINE_VALUE
        if "Recruiting" in service:
            base = 7500.0
        elif "Support" in service:
            base = 6000.0
        elif "Analytics" in service:
            base = 8000.0
        score = float(brief.get("revenue_ready_score") or 0)
        return round(base * (0.9 + min(score, 100) / 500.0), 2)
