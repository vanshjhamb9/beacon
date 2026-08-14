from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from founder_os.models.types import (
    FounderOsInput,
    RevenueTask,
    TaskKind,
    TaskPriority,
    TaskStatus,
)


class RevenueTaskEngine:
    """Auto-create founder tasks from existing queue/campaign/inbox signals."""

    def generate(self, data: FounderOsInput) -> list[RevenueTask]:
        now = data.now or datetime.now(UTC)
        tasks: list[RevenueTask] = []

        for row in data.pending_campaigns:
            tasks.append(
                self._task(
                    kind=TaskKind.APPROVE_CAMPAIGN,
                    title=f"Approve campaign — {row.get('company_name', 'company')}",
                    priority=TaskPriority.P0,
                    deadline=now + timedelta(hours=4),
                    reason="Campaign is waiting founder approval before send.",
                    evidence=[f"campaign_id:{row.get('id')}", f"status:{row.get('status', 'needs_review')}"],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                    related_id=str(row.get("id") or ""),
                )
            )

        for row in data.pending_replies:
            tasks.append(
                self._task(
                    kind=TaskKind.REPLY_NEEDED,
                    title=f"Reply needed — {row.get('company_name', 'inbox')}",
                    priority=TaskPriority.P0,
                    deadline=now + timedelta(hours=2),
                    reason="Inbound reply waiting — reply rate depends on speed.",
                    evidence=[f"thread_id:{row.get('id')}", "channel:inbox"],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                    related_id=str(row.get("id") or ""),
                )
            )

        for row in data.meetings:
            tasks.append(
                self._task(
                    kind=TaskKind.MEETING_TODAY,
                    title=f"Meeting today — {row.get('company_name', 'meeting')}",
                    priority=TaskPriority.P0,
                    deadline=self._parse_dt(row.get("scheduled_at")) or now + timedelta(hours=1),
                    reason="Scheduled meeting requires prep and closing strategy.",
                    evidence=[f"meeting_id:{row.get('id')}", f"scheduled_at:{row.get('scheduled_at')}"],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                    related_id=str(row.get("id") or ""),
                )
            )

        for row in data.proposal_candidates:
            tasks.append(
                self._task(
                    kind=TaskKind.PROPOSAL_REQUIRED,
                    title=f"Proposal required — {row.get('company_name', 'account')}",
                    priority=TaskPriority.P1,
                    deadline=now + timedelta(days=2),
                    reason="Account is ready for scoped proposal.",
                    evidence=[f"service:{row.get('recommended_service')}", f"budget:{row.get('budget_range')}"],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                    related_id=str(row.get("opportunity_id") or row.get("id") or ""),
                )
            )

        for row in data.follow_ups:
            tasks.append(
                self._task(
                    kind=TaskKind.FOLLOW_UP_TODAY,
                    title=f"Follow-up today — {row.get('company_name', 'account')}",
                    priority=TaskPriority.P1,
                    deadline=now + timedelta(hours=8),
                    reason="Follow-up window is open today.",
                    evidence=[f"why:{row.get('why_today') or 'scheduled_follow_up'}"],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                    related_id=str(row.get("id") or ""),
                )
            )

        for row in data.work_queue_items:
            if str(row.get("status", "pending")) != "pending":
                continue
            tasks.append(
                self._task(
                    kind=TaskKind.REVIEW_EMAIL,
                    title=f"Review outreach — {row.get('company_name', 'account')}",
                    priority=TaskPriority.P1,
                    deadline=now + timedelta(hours=6),
                    reason="Work queue item awaiting approve/send.",
                    evidence=[f"grade:{row.get('priority_grade')}", f"service:{row.get('recommended_service')}"],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                    related_id=str(row.get("id") or ""),
                )
            )

        for row in data.missing_contacts:
            tasks.append(
                self._task(
                    kind=TaskKind.LEAD_MISSING_CONTACT,
                    title=f"Missing contact — {row.get('company_name', 'account')}",
                    priority=TaskPriority.P2,
                    deadline=now + timedelta(days=1),
                    reason="Sales-ready account lacks email/phone for outreach.",
                    evidence=["missing_contact:true"],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                )
            )

        for row in data.website_audit_needed:
            tasks.append(
                self._task(
                    kind=TaskKind.WEBSITE_AUDIT_REQUIRED,
                    title=f"Website audit — {row.get('company_name', 'account')}",
                    priority=TaskPriority.P2,
                    deadline=now + timedelta(days=2),
                    reason="Website intelligence flagged high-severity issues.",
                    evidence=[str(e) for e in (row.get("evidence") or ["website_audit:required"])][:6],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                )
            )

        for row in data.verification_failed:
            tasks.append(
                self._task(
                    kind=TaskKind.VERIFICATION_FAILED,
                    title=f"Verification failed — {row.get('company_name', 'account')}",
                    priority=TaskPriority.P2,
                    deadline=now + timedelta(days=1),
                    reason="Data verification failed — do not pitch until fixed.",
                    evidence=[f"verification_score:{row.get('verification_score', 0)}"],
                    company_id=row.get("company_id"),
                    company_name=row.get("company_name"),
                )
            )

        priority_order = {TaskPriority.P0: 0, TaskPriority.P1: 1, TaskPriority.P2: 2, TaskPriority.P3: 3}
        tasks.sort(key=lambda t: (priority_order[t.priority], t.title))
        return tasks

    def _task(
        self,
        *,
        kind: TaskKind,
        title: str,
        priority: TaskPriority,
        deadline: datetime | None,
        reason: str,
        evidence: list[str],
        company_id: object = None,
        company_name: object = None,
        related_id: str | None = None,
    ) -> RevenueTask:
        cid: UUID | None = None
        if company_id is not None:
            try:
                cid = company_id if isinstance(company_id, UUID) else UUID(str(company_id))
            except (TypeError, ValueError):
                cid = None
        return RevenueTask(
            task_id=str(uuid4()),
            kind=kind,
            title=title,
            priority=priority,
            deadline=deadline,
            owner="founder",
            status=TaskStatus.OPEN,
            reason=reason,
            evidence=[e for e in evidence if e],
            company_id=cid,
            company_name=str(company_name) if company_name else None,
            related_id=related_id or None,
        )

    def _parse_dt(self, value: object) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
