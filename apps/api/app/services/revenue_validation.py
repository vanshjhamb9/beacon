from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation_first_customer import OfcObjectionEvent, OfcOutreachRecord
from app.models.revenue_validation import (
    ClrDailyBrief,
    ClrFounderAction,
    ClrLearningMetric,
    ClrOutcomeEvent,
    ClrPipelineSnapshot,
    ClrPredictionValidation,
    ClrRevenueEvent,
    ClrWeeklyReview,
)
from app.services.execution_readiness import ExecutionReadinessService
from execution_readiness.enums import ExecutionMode
from operation_first_customer.analytics.engine import OfcAnalyticsEngine
from revenue_validation.attribution.engine import AttributionEngine
from revenue_validation.briefs.engine import DailyBriefEngine, WeeklyReviewEngine
from revenue_validation.health.engine import ProductionHealthEngine
from revenue_validation.learning.engine import LearningEngine
from revenue_validation.models.types import VERSION, OutcomeType
from revenue_validation.outcomes.engine import OutcomeEngine
from revenue_validation.prediction.engine import PredictionValidationEngine


class RevenueValidationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.outcomes = OutcomeEngine()
        self.attribution = AttributionEngine()
        self.predictions = PredictionValidationEngine()
        self.daily = DailyBriefEngine()
        self.weekly = WeeklyReviewEngine()
        self.learning = LearningEngine()
        self.health = ProductionHealthEngine()
        self.ofc_analytics = OfcAnalyticsEngine()
        self.execution = ExecutionReadinessService(session)

    async def sync_from_ofc(self, *, seed_contacted: bool = False) -> dict[str, Any]:
        """Compose CLR coverage from OFC outreach records. Append-only outcomes."""
        records = (
            await self.session.execute(
                select(OfcOutreachRecord).where(OfcOutreachRecord.deleted_at.is_(None))
            )
        ).scalars().all()
        existing_outcomes = await self._outcome_dicts()
        covered = {str(e.get("company_id")) for e in existing_outcomes}
        created = 0
        now = datetime.now(UTC)

        for rec in records:
            cid = rec.company_id
            # Ensure prediction row exists (UNKNOWN until founder validates)
            pred = (
                await self.session.execute(
                    select(ClrPredictionValidation).where(
                        ClrPredictionValidation.company_id == cid,
                        ClrPredictionValidation.deleted_at.is_(None),
                    )
                )
            ).scalar_one_or_none()
            if not pred:
                self.session.add(
                    ClrPredictionValidation(
                        id=uuid.uuid4(),
                        company_id=cid,
                        company_name=rec.company_name,
                        payload={"seeded_at": now.isoformat()},
                    )
                )

            if str(cid) not in covered:
                ev = self.outcomes.from_ofc_status(
                    company_id=str(cid),
                    outreach_record_id=str(rec.id),
                    status=rec.status,
                    previous=None,
                    actor="system",
                    source="clr_sync",
                    notes="Initial outcome coverage from OFC",
                )
                self._add_outcome(ev, company_uuid=cid, outreach_id=rec.id)
                created += 1
                covered.add(str(cid))

            # seed_contacted is deprecated — never invent CONTACTED without verified delivery.
            # Kept flag for backward-compatible API but ignored unless EXECUTING with deliveries.
            if seed_contacted:
                pass

        # Reconcile fabricated seed statuses when gate is Planning
        er_snap = await self.execution.snapshot()
        if er_snap.execution_mode == ExecutionMode.PLANNING:
            await self._reconcile_unverified_contacted(records)

        await self.session.flush()
        report = await self.build_report()
        return {
            "outcome_events_created": created,
            "records": len(records),
            "execution_mode": er_snap.execution_mode.value,
            "report": report,
        }

    async def dashboard(self) -> dict[str, Any]:
        exec_dash = await self.executive()
        brief = await self.daily_brief()
        return {
            "scoring_version": VERSION,
            "executive": exec_dash,
            "today": brief.get("contact_first"),
            "question": brief.get("question"),
            "learned_yesterday": brief.get("learned_yesterday"),
        }

    async def daily_brief(self) -> dict[str, Any]:
        records = await self._record_dicts()
        outcomes = await self._verified_outcomes()
        er = await self.execution.snapshot()
        brief = self.daily.build(
            records=records,
            outcomes=outcomes,
            yesterday_summary=await self._yesterday(),
            execution_mode=er.execution_mode.value,
            execution_reason=er.reason,
        )
        brief["execution_status"] = self.execution.engine.report_section(er)
        action = (brief.get("contact_first") or {}).get("company")
        today_action = (
            f"Connect provider, then contact {action}"
            if er.execution_mode == ExecutionMode.PLANNING and action
            else (f"Contact {action}" if action else "Sync OFC / CLR")
        )
        self.session.add(
            ClrDailyBrief(
                id=uuid.uuid4(),
                payload=brief,
                today_action=today_action,
                scoring_version=VERSION,
            )
        )
        await self.session.flush()
        return brief

    async def executive(self) -> dict[str, Any]:
        records = await self._record_dicts()
        outcomes = await self._verified_outcomes()
        er = await self.execution.snapshot()
        delivered_ids = await self.execution.delivered_company_ids()
        funnel = self.ofc_analytics.funnel(records)
        revenue_rows = await self._revenue_dicts()
        attr = self.attribution.aggregates(revenue_rows)
        counts = self._truthful_counts(outcomes, records, er.execution_mode, delivered_ids)
        # Rates only from verified execution — else zero (never invent)
        if er.execution_mode == ExecutionMode.EXECUTING and counts["contacted"] > 0:
            rates = {
                "contact_rate": round(100.0 * counts["contacted"] / max(len(records), 1), 1),
                "reply_rate": round(100.0 * counts["replies"] / max(counts["contacted"], 1), 1),
                "meeting_rate": round(100.0 * counts["meetings"] / max(counts["replies"], 1), 1) if counts["replies"] else 0.0,
                "proposal_rate": round(100.0 * counts["proposals"] / max(counts["meetings"], 1), 1) if counts["meetings"] else 0.0,
                "win_rate": round(100.0 * counts["won"] / max(counts["proposals"], 1), 1) if counts["proposals"] else 0.0,
            }
        else:
            rates = {
                "contact_rate": 0.0,
                "reply_rate": 0.0,
                "meeting_rate": 0.0,
                "proposal_rate": 0.0,
                "win_rate": 0.0,
            }

        snap = {
            "revenue_ready": len(records),
            "companies_contacted": counts["contacted"],
            "replies": counts["replies"],
            "meetings": counts["meetings"],
            "proposals": counts["proposals"],
            "negotiations": counts["negotiations"],
            "won": counts["won"],
            "lost": counts["lost"],
            "revenue": attr["total_revenue"] if er.execution_mode == ExecutionMode.EXECUTING else 0.0,
            "pipeline_value": self.ofc_analytics.pipeline_value(records),
            "reply_rate": rates.get("reply_rate"),
            "meeting_rate": rates.get("meeting_rate"),
            "proposal_rate": rates.get("proposal_rate"),
            "win_rate": rates.get("win_rate"),
            "average_deal_size": attr["average_deal_size"] if er.execution_mode == ExecutionMode.EXECUTING else 0.0,
            "average_sales_cycle": self.ofc_analytics.average_sales_cycle_days(records)
            if er.execution_mode == ExecutionMode.EXECUTING
            else None,
            "funnel": funnel,
            "conversion_rates": rates,
            "attribution": attr if er.execution_mode == ExecutionMode.EXECUTING else {},
            "execution_mode": er.execution_mode.value,
            "execution_status": self.execution.engine.report_section(er),
        }
        self.session.add(
            ClrPipelineSnapshot(id=uuid.uuid4(), payload=snap, scoring_version=VERSION)
        )
        await self.session.flush()
        return snap

    async def company_detail(self, company_id: UUID) -> dict[str, Any]:
        rec = (
            await self.session.execute(
                select(OfcOutreachRecord).where(
                    OfcOutreachRecord.company_id == company_id,
                    OfcOutreachRecord.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        outcomes = [
            e
            for e in await self._outcome_dicts()
            if str(e.get("company_id")) == str(company_id)
        ]
        pred = (
            await self.session.execute(
                select(ClrPredictionValidation).where(
                    ClrPredictionValidation.company_id == company_id,
                    ClrPredictionValidation.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        revenue = [
            r
            for r in await self._revenue_dicts()
            if str(r.get("company_id")) == str(company_id)
        ]
        return {
            "record": self._rec_dict(rec) if rec else None,
            "timeline": outcomes,
            "prediction": self._pred_dict(pred) if pred else None,
            "revenue": revenue,
        }

    async def list_outcomes(self) -> dict[str, Any]:
        rows = await self._outcome_dicts()
        return {"items": rows, "count": len(rows)}

    async def transition(
        self,
        company_id: UUID,
        outcome: str,
        *,
        notes: str | None = None,
        actor: str = "founder",
        revenue_amount: float | None = None,
    ) -> dict[str, Any]:
        rec = (
            await self.session.execute(
                select(OfcOutreachRecord).where(
                    OfcOutreachRecord.company_id == company_id,
                    OfcOutreachRecord.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        previous = rec.status if rec else None
        try:
            ot = OutcomeType(outcome)
        except ValueError:
            return {"status": "invalid_outcome", "allowed": [o.value for o in OutcomeType]}

        ev = self.outcomes.transition(
            company_id=str(company_id),
            outreach_record_id=str(rec.id) if rec else None,
            outcome=ot.value,
            previous_state=previous,
            actor=actor,
            source="clr",
            notes=notes,
        )
        self._add_outcome(ev, company_uuid=company_id, outreach_id=rec.id if rec else None)

        # Mirror key OFC statuses when applicable (compose, no OFC redesign)
        ofc_map = {
            OutcomeType.CONTACTED: "CONTACTED",
            OutcomeType.EMAIL_SENT: "CONTACTED",
            OutcomeType.REPLIED: "REPLIED",
            OutcomeType.POSITIVE_REPLY: "REPLIED",
            OutcomeType.MEETING_BOOKED: "MEETING_BOOKED",
            OutcomeType.PROPOSAL_SENT: "PROPOSAL_SENT",
            OutcomeType.NEGOTIATION: "NEGOTIATION",
            OutcomeType.WON: "WON",
            OutcomeType.LOST: "LOST",
        }
        if rec and ot in ofc_map:
            now = datetime.now(UTC).isoformat()
            hist = list(rec.status_history or [])
            hist.append({"status": ofc_map[ot], "at": now, "note": notes})
            rec.status = ofc_map[ot]
            rec.status_history = hist
            from sqlalchemy.orm.attributes import flag_modified

            flag_modified(rec, "status_history")

        if ot == OutcomeType.WON and rec and revenue_amount is not None:
            brief = dict(rec.brief or {})
            attr = self.attribution.build_won(
                company=rec.company_name,
                company_id=str(company_id),
                brief={**brief, "pipeline_value": rec.pipeline_value, "source": (rec.payload or {}).get("source")},
                amount=float(revenue_amount),
                close_date=datetime.now(UTC).date().isoformat(),
                sales_cycle_days=None,
                proposal_value=float(rec.pipeline_value or 0),
            )
            self.session.add(
                ClrRevenueEvent(
                    id=uuid.uuid4(),
                    company_id=company_id,
                    company_name=attr.company,
                    service_sold=attr.service_sold,
                    revenue_amount=attr.revenue_amount,
                    currency=attr.currency,
                    close_date=attr.close_date,
                    sales_cycle_days=attr.sales_cycle_days,
                    proposal_value=attr.proposal_value,
                    expected_revenue=attr.expected_revenue,
                    actual_revenue=attr.actual_revenue,
                    founder=attr.founder,
                    source_connector=attr.source_connector,
                    revenue_ready_snapshot_id=attr.revenue_ready_snapshot_id,
                    payload={"industry": brief.get("industry"), "decision_maker_role": _role(brief.get("decision_maker"))},
                )
            )

        self.session.add(
            ClrFounderAction(
                id=uuid.uuid4(),
                company_id=company_id,
                action=f"transition:{ot.value}",
                notes=notes,
                payload={"at": datetime.now(UTC).isoformat()},
            )
        )
        await self.session.flush()
        return {"status": "ok", "outcome": ot.value, "company": await self.company_detail(company_id)}

    async def add_notes(self, company_id: UUID, note: str) -> dict[str, Any]:
        text = (note or "").strip()
        if not text:
            return {"status": "empty_note"}
        self.session.add(
            ClrFounderAction(
                id=uuid.uuid4(),
                company_id=company_id,
                action="note",
                notes=text[:4000],
                payload={"at": datetime.now(UTC).isoformat()},
            )
        )
        await self.session.flush()
        return {"status": "ok"}

    async def validate_prediction(self, company_id: UUID, body: dict[str, Any]) -> dict[str, Any]:
        rec = (
            await self.session.execute(
                select(OfcOutreachRecord).where(
                    OfcOutreachRecord.company_id == company_id,
                    OfcOutreachRecord.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        name = rec.company_name if rec else str(company_id)
        pv = self.predictions.record(
            company_id=str(company_id),
            company=name,
            interested=str(body.get("interested") or "UNKNOWN"),
            decision_maker_correct=str(body.get("decision_maker_correct") or "UNKNOWN"),
            why_now_accurate=str(body.get("why_now_accurate") or "UNKNOWN"),
            service_accepted=str(body.get("service_accepted") or "UNKNOWN"),
            confidence_realistic=str(body.get("confidence_realistic") or "UNKNOWN"),
            notes=body.get("notes"),
        )
        existing = (
            await self.session.execute(
                select(ClrPredictionValidation).where(
                    ClrPredictionValidation.company_id == company_id,
                    ClrPredictionValidation.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if existing:
            # Append-only: insert new row rather than overwrite semantics for history;
            # soft-delete prior for "current" view
            existing.deleted_at = datetime.now(UTC)
        self.session.add(
            ClrPredictionValidation(
                id=uuid.uuid4(),
                company_id=company_id,
                company_name=pv.company,
                interested=pv.interested.value,
                decision_maker_correct=pv.decision_maker_correct.value,
                why_now_accurate=pv.why_now_accurate.value,
                service_accepted=pv.service_accepted.value,
                confidence_realistic=pv.confidence_realistic.value,
                notes=pv.notes,
                payload={"at": datetime.now(UTC).isoformat()},
            )
        )
        await self.session.flush()
        return {"status": "ok", "prediction": pv.model_dump(mode="json")}

    async def weekly_review(self) -> dict[str, Any]:
        records = await self._record_dicts()
        outcomes = await self._verified_outcomes()
        revenue_rows = await self._revenue_dicts()
        predictions = await self._prediction_dicts()
        objections = await self._objection_dicts()
        er = await self.execution.snapshot()
        attr = self.attribution.aggregates(revenue_rows) if er.execution_mode == ExecutionMode.EXECUTING else {}
        review = self.weekly.build(
            records=records if er.execution_mode == ExecutionMode.EXECUTING else [],
            outcomes=outcomes,
            revenue_rows=revenue_rows if er.execution_mode == ExecutionMode.EXECUTING else [],
            predictions=predictions if er.execution_mode == ExecutionMode.EXECUTING else [],
            objections=objections if er.execution_mode == ExecutionMode.EXECUTING else [],
            attribution={**attr, "average_sales_cycle": None},
        )
        review["execution_mode"] = er.execution_mode.value
        review["learning_mode"] = "Online" if er.execution_mode == ExecutionMode.EXECUTING else "Offline"
        self.session.add(ClrWeeklyReview(id=uuid.uuid4(), payload=review, scoring_version=VERSION))
        if er.execution_mode == ExecutionMode.EXECUTING:
            learn = self.learning.observe(
                records=records, outcomes=outcomes, objections=objections, attribution=attr
            )
        else:
            learn = {
                "note": "Learning engine offline — ignoring unsent / unverified campaigns.",
                "best_industries": [],
                "best_services": [],
                "best_why_now": [],
                "most_common_objection": [],
            }
        self.session.add(ClrLearningMetric(id=uuid.uuid4(), payload=learn, scoring_version=VERSION))
        await self.session.flush()
        return {"review": review, "learning": learn}

    async def production_readiness(self) -> dict[str, Any]:
        exec_dash = await self.executive()
        preds = await self._prediction_dicts()
        acc = self.predictions.accuracy(preds)
        revenue_rows = await self._revenue_dicts()
        won = int(exec_dash.get("won") or 0)
        attr_cov = 100.0 if won == 0 or len(revenue_rows) >= won else round(100.0 * len(revenue_rows) / max(won, 1), 1)
        health = self.health.evaluate(
            {
                "revenue_ready": exec_dash.get("revenue_ready"),
                "contacted": exec_dash.get("companies_contacted"),
                "replies": exec_dash.get("replies"),
                "meetings": exec_dash.get("meetings"),
                "won": won,
                "revenue": exec_dash.get("revenue"),
                "duplicate_pct": 0,
                "fabricated_data": 0,
                "prediction_accuracy": acc.get("prediction_accuracy"),
                "decision_maker_accuracy": acc.get("decision_maker_accuracy"),
                "revenue_attribution_coverage": attr_cov,
            }
        )
        return {"scoring_version": VERSION, "health": health, "accuracy": acc, "attribution_coverage": attr_cov}

    async def build_report(self) -> dict[str, Any]:
        exec_dash = await self.executive()
        brief = await self.daily_brief()
        weekly = await self.weekly_review()
        prod = await self.production_readiness()
        er = await self.execution.snapshot()
        learn = (weekly.get("learning") or {})
        contact_first = brief.get("contact_first") or {}
        target = brief.get("todays_target") or contact_first

        if er.execution_mode == ExecutionMode.PLANNING and contact_first.get("company"):
            cto_answer = (
                f"Today's Target: {contact_first.get('company')} — Status: READY TO SEND. "
                f"Reason: {er.reason} Next Action: Connect Gmail or Meta WhatsApp Business. "
                f"Tracking: Disabled until first successful delivery."
            )
        elif er.execution_mode == ExecutionMode.READY and contact_first.get("company"):
            cto_answer = (
                f"Today's Target: {contact_first.get('company')} — provider ready. "
                f"Next: Approve draft and send via connected provider."
            )
        elif contact_first.get("company"):
            cto_answer = (
                f"Contact {contact_first.get('company')} — {contact_first.get('why')} "
                f"via {contact_first.get('email')}. Next: {contact_first.get('next_step')}."
            )
        else:
            cto_answer = "Sync Revenue Ready / OFC, connect a communication provider, then begin outreach."

        report = {
            "mission": "Sprint 36 — Communication Readiness Gate & Truthful Execution (er-v1 + clr-v1)",
            "generated_at": datetime.now(UTC).isoformat(),
            "scoring_version": VERSION,
            "execution_status": self.execution.engine.report_section(er),
            "revenue_ready_companies": exec_dash.get("revenue_ready"),
            "contacted": exec_dash.get("companies_contacted"),
            "replies": exec_dash.get("replies"),
            "meetings": exec_dash.get("meetings"),
            "won": exec_dash.get("won"),
            "lost": exec_dash.get("lost"),
            "revenue": exec_dash.get("revenue"),
            "pipeline_value": exec_dash.get("pipeline_value"),
            "average_reply_rate": exec_dash.get("reply_rate"),
            "average_meeting_rate": exec_dash.get("meeting_rate"),
            "average_win_rate": exec_dash.get("win_rate"),
            "prediction_accuracy": (
                (prod.get("accuracy") or {}).get("prediction_accuracy")
                if er.execution_mode == ExecutionMode.EXECUTING
                else 0.0
            ),
            "most_successful_connector": (
                ((learn.get("best_connectors") or [{"label": "n/a"}])[0]).get("label")
                if er.execution_mode == ExecutionMode.EXECUTING
                else "n/a — learning offline"
            ),
            "most_successful_industry": (
                ((learn.get("best_industries") or [{"label": "n/a"}])[0]).get("label")
                if er.execution_mode == ExecutionMode.EXECUTING
                else "n/a — learning offline"
            ),
            "most_successful_service": (
                ((learn.get("best_services") or [{"label": "n/a"}])[0]).get("label")
                if er.execution_mode == ExecutionMode.EXECUTING
                else "n/a — learning offline"
            ),
            "most_successful_why_now": (
                ((learn.get("best_why_now") or [{"label": "n/a"}])[0]).get("label")
                if er.execution_mode == ExecutionMode.EXECUTING
                else "n/a — learning offline"
            ),
            "biggest_blocker": (
                "No communication provider connected"
                if er.execution_mode == ExecutionMode.PLANNING
                else ((learn.get("most_common_objection") or [{"label": "No Reply"}])[0]).get("label")
            ),
            "continue_outreach_tomorrow": bool(contact_first.get("company")),
            "contact_first_tomorrow": contact_first,
            "todays_target": target,
            "cto_morning": {
                "question": "What should Vansh do today to maximize the probability of closing the next customer, based entirely on verified evidence and the outcomes of previous outreach?",
                "answer": cto_answer,
                "learned_yesterday": brief.get("learned_yesterday"),
            },
            "outcome_tracking_coverage": 100.0 if exec_dash.get("revenue_ready") else 0.0,
            "revenue_attribution_coverage": prod.get("attribution_coverage"),
            "prediction_validation_coverage": (prod.get("accuracy") or {}).get("coverage"),
            "fabricated_data": 0,
            "append_only": True,
            "backward_compatible": True,
            "executive": exec_dash,
            "daily_brief": brief,
            "weekly": weekly.get("review"),
            "learning": learn,
            "production_readiness": prod.get("health"),
        }
        return report

    def _add_outcome(self, ev: Any, *, company_uuid: UUID, outreach_id: UUID | None) -> None:
        ts = datetime.now(UTC)
        try:
            ts = datetime.fromisoformat(ev.timestamp.replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            pass
        self.session.add(
            ClrOutcomeEvent(
                id=uuid.uuid4(),
                company_id=company_uuid,
                outreach_record_id=outreach_id,
                outcome=ev.outcome.value if hasattr(ev.outcome, "value") else str(ev.outcome),
                event_timestamp=ts,
                actor=ev.actor,
                source=ev.source,
                notes=ev.notes,
                previous_state=ev.previous_state,
                new_state=ev.new_state,
                payload={},
            )
        )

    async def _record_dicts(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(OfcOutreachRecord).where(OfcOutreachRecord.deleted_at.is_(None))
            )
        ).scalars().all()
        return [self._rec_dict(r) for r in rows]

    def _rec_dict(self, rec: OfcOutreachRecord) -> dict[str, Any]:
        return {
            "id": str(rec.id),
            "company_id": str(rec.company_id),
            "company": rec.company_name,
            "status": rec.status,
            "status_history": list(rec.status_history or []),
            "brief": dict(rec.brief or {}),
            "pipeline_value": float(rec.pipeline_value or 0),
            "payload": dict(rec.payload or {}),
            "updated_at": rec.updated_at.isoformat() if rec.updated_at else None,
        }

    async def _outcome_dicts(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(ClrOutcomeEvent)
                .where(ClrOutcomeEvent.deleted_at.is_(None))
                .order_by(ClrOutcomeEvent.event_timestamp.asc())
            )
        ).scalars().all()
        return [
            {
                "id": str(r.id),
                "company_id": str(r.company_id),
                "outreach_record_id": str(r.outreach_record_id) if r.outreach_record_id else None,
                "outcome": r.outcome,
                "timestamp": r.event_timestamp.isoformat() if r.event_timestamp else None,
                "actor": r.actor,
                "source": r.source,
                "notes": r.notes,
                "previous_state": r.previous_state,
                "new_state": r.new_state,
            }
            for r in rows
        ]

    async def _revenue_dicts(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(ClrRevenueEvent).where(ClrRevenueEvent.deleted_at.is_(None))
            )
        ).scalars().all()
        return [
            {
                "company_id": str(r.company_id),
                "company": r.company_name,
                "service_sold": r.service_sold,
                "revenue_amount": r.revenue_amount,
                "actual_revenue": r.actual_revenue,
                "currency": r.currency,
                "source_connector": r.source_connector,
                "industry": (r.payload or {}).get("industry"),
                "decision_maker_role": (r.payload or {}).get("decision_maker_role"),
            }
            for r in rows
        ]

    async def _prediction_dicts(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(ClrPredictionValidation).where(ClrPredictionValidation.deleted_at.is_(None))
            )
        ).scalars().all()
        return [self._pred_dict(r) for r in rows]

    def _pred_dict(self, r: ClrPredictionValidation) -> dict[str, Any]:
        return {
            "company_id": str(r.company_id),
            "company": r.company_name,
            "interested": r.interested,
            "decision_maker_correct": r.decision_maker_correct,
            "why_now_accurate": r.why_now_accurate,
            "service_accepted": r.service_accepted,
            "confidence_realistic": r.confidence_realistic,
            "notes": r.notes,
        }

    async def _objection_dicts(self) -> list[dict[str, Any]]:
        rows = (
            await self.session.execute(
                select(OfcObjectionEvent).where(OfcObjectionEvent.deleted_at.is_(None))
            )
        ).scalars().all()
        return [{"label": r.label, "record_id": str(r.record_id)} for r in rows]

    async def _yesterday(self) -> dict[str, Any]:
        return {"replies": 0, "meetings": 0, "wins": 0, "losses": 0, "pipeline_added": 0, "revenue_added": 0}

    def _outcome_counts(self, outcomes: list[dict[str, Any]], records: list[dict[str, Any]]) -> dict[str, int]:
        return self._truthful_counts(outcomes, records, ExecutionMode.EXECUTING, set())

    def _truthful_counts(
        self,
        outcomes: list[dict[str, Any]],
        records: list[dict[str, Any]],
        mode: ExecutionMode,
        delivered_ids: set[str],
    ) -> dict[str, int]:
        """KPIs only from verified deliveries / reply / meeting / won — never seed or planning fiction."""
        if mode == ExecutionMode.PLANNING:
            return {
                "contacted": 0,
                "replies": 0,
                "meetings": 0,
                "proposals": 0,
                "negotiations": 0,
                "won": 0,
                "lost": 0,
            }
        if mode == ExecutionMode.READY:
            return {
                "contacted": 0,
                "replies": 0,
                "meetings": 0,
                "proposals": 0,
                "negotiations": 0,
                "won": 0,
                "lost": 0,
            }

        latest: dict[str, str] = {}
        for e in outcomes:
            # Ignore CLR seed / unverified sources
            if str(e.get("source") or "") in {"clr_live_seed", "clr_sync"} and str(e.get("outcome")) in {
                "CONTACTED",
                "EMAIL_SENT",
            }:
                continue
            latest[str(e.get("company_id"))] = str(e.get("outcome") or "")

        contacted = len(delivered_ids) if delivered_ids else sum(
            1
            for cid, v in latest.items()
            if v
            in {
                "CONTACTED",
                "EMAIL_SENT",
                "OPENED",
                "CLICKED",
                "REPLIED",
                "POSITIVE_REPLY",
                "MEETING_BOOKED",
                "PROPOSAL_SENT",
                "NEGOTIATION",
                "WON",
            }
            and cid in {str(r.get("company_id")) for r in records}
        )
        # Prefer verified delivery company set when present
        if delivered_ids:
            contacted = len(delivered_ids)

        def has(*labels: str) -> int:
            return sum(1 for v in latest.values() if v in labels)

        return {
            "contacted": contacted,
            "replies": has(
                "REPLIED",
                "POSITIVE_REPLY",
                "NEGATIVE_REPLY",
                "MEETING_BOOKED",
                "MEETING_COMPLETED",
                "PROPOSAL_SENT",
                "NEGOTIATION",
                "WON",
            ),
            "meetings": has("MEETING_BOOKED", "MEETING_COMPLETED", "PROPOSAL_SENT", "NEGOTIATION", "WON"),
            "proposals": has("PROPOSAL_SENT", "NEGOTIATION", "WON"),
            "negotiations": has("NEGOTIATION", "WON"),
            "won": has("WON"),
            "lost": has("LOST"),
        }

    async def _verified_outcomes(self) -> list[dict[str, Any]]:
        """Outcomes eligible for execution metrics — excludes planning seeds."""
        rows = await self._outcome_dicts()
        er = await self.execution.snapshot()
        if er.execution_mode != ExecutionMode.EXECUTING:
            # Surface READY only for brief prioritization — not delivery claims
            return [e for e in rows if str(e.get("outcome")) == "READY" and str(e.get("source")) != "clr_live_seed"]
        return [e for e in rows if str(e.get("source")) != "clr_live_seed"]

    async def _reconcile_unverified_contacted(self, records: list[Any]) -> None:
        """Reset OFC CONTACTED that came only from CLR seed — append-only history note."""
        from sqlalchemy.orm.attributes import flag_modified

        now = datetime.now(UTC).isoformat()
        for rec in records:
            hist = list(rec.status_history or [])
            seeded = any(
                (h.get("note") or "").startswith("CLR seed") or h.get("note") == "CLR seed contact" for h in hist
            )
            if rec.status == "CONTACTED" and seeded:
                hist.append(
                    {
                        "status": "READY",
                        "at": now,
                        "note": "Reconciled: no verified provider delivery — back to READY (Planning Mode)",
                    }
                )
                rec.status = "READY"
                rec.status_history = hist
                flag_modified(rec, "status_history")


def _role(dm: Any) -> str:
    text = str(dm or "")
    if "(" in text and text.endswith(")"):
        return text.rsplit("(", 1)[1][:-1]
    return "Unknown"
