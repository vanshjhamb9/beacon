"""Deterministic company journey assembly — no AI, no scoring models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from intelligence_center.models import (
    JOURNEY_STAGES,
    STAGE_LABELS,
    CompanyJourney,
    JourneyStage,
)


def _duration(start: datetime | None, end: datetime | None) -> float | None:
    if not start or not end:
        return None
    return round(max((end - start).total_seconds(), 0.0), 2)


def build_journey_stages(facts: dict[str, Any]) -> list[JourneyStage]:
    """
    facts keys (optional):
      signal_at, signal_connector, signal_evidence, signal_worker
      identity_at, identity_connector, identity_evidence, ...
      website_*, email_*, decision_maker_*, sales_ready_*, revenue_ready_*
      outreach_*, reply_*, meeting_*, proposal_*, won_*, lost_at
      retries: dict[stage, int]
      failures: dict[stage, list[str]]
    """
    retries: dict[str, int] = facts.get("retries") or {}
    failures: dict[str, list[str]] = facts.get("failures") or {}
    lost = bool(facts.get("lost_at"))

    stages: list[JourneyStage] = []
    for stage in JOURNEY_STAGES:
        completed_at = facts.get(f"{stage}_at")
        started_at = facts.get(f"{stage}_started_at") or completed_at
        evidence = list(facts.get(f"{stage}_evidence") or [])
        connector = facts.get(f"{stage}_connector")
        worker = facts.get(f"{stage}_worker")
        detail = str(facts.get(f"{stage}_detail") or "")

        # Won and Lost are mutually exclusive terminals.
        if stage == "won" and lost and not completed_at:
            status = "skipped"
        elif stage == "lost":
            if completed_at or lost:
                status = "completed"
                completed_at = completed_at or facts.get("lost_at")
                started_at = started_at or completed_at
            else:
                # Lost is an alternate terminal — never "pending" just because outreach ran.
                status = "skipped"
        elif completed_at:
            status = "completed"
        elif failures.get(stage):
            status = "failed"
        else:
            # pending if prior stage completed, else skipped (not yet reached)
            prior_ok = True
            idx = JOURNEY_STAGES.index(stage)
            if idx > 0:
                prior = JOURNEY_STAGES[idx - 1]
                # Skip over the opposite terminal when checking prior completion.
                if prior in {"won", "lost"}:
                    prior_ok = bool(facts.get("proposal_at") or facts.get("meeting_at"))
                else:
                    prior_ok = bool(facts.get(f"{prior}_at"))
            status = "pending" if prior_ok else "skipped"

        stages.append(
            JourneyStage(
                stage=stage,
                label=STAGE_LABELS.get(stage, stage.replace("_", " ").title()),
                status=status,
                started_at=started_at if isinstance(started_at, datetime) else None,
                completed_at=completed_at if isinstance(completed_at, datetime) else None,
                duration_seconds=_duration(
                    started_at if isinstance(started_at, datetime) else None,
                    completed_at if isinstance(completed_at, datetime) else None,
                ),
                connector=str(connector) if connector else None,
                worker=str(worker) if worker else None,
                evidence=[str(e) for e in evidence],
                retry_count=int(retries.get(stage, 0) or 0),
                failures=list(failures.get(stage) or []),
                detail=detail,
            )
        )
    return stages


def current_stage_name(stages: list[JourneyStage]) -> str:
    last_completed = "signal"
    for stage in stages:
        if stage.status == "completed":
            last_completed = stage.stage
            if stage.stage in {"won", "lost"}:
                return stage.stage
        elif stage.status in {"pending", "failed"}:
            return stage.stage
    return last_completed


def pipeline_health_view(stages: list[JourneyStage]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for stage in stages:
        mark = "✔" if stage.status == "completed" else ("✗" if stage.status == "failed" else ("Pending" if stage.status == "pending" else "—"))
        out.append(
            {
                "stage": stage.stage,
                "label": stage.label,
                "status": stage.status,
                "mark": mark,
                "timestamp": stage.completed_at.isoformat() if stage.completed_at else None,
                "duration_seconds": stage.duration_seconds,
                "connector": stage.connector,
                "worker": stage.worker,
                "evidence": stage.evidence,
                "retry_count": stage.retry_count,
                "failures": stage.failures,
            }
        )
    return out


def assemble_company_journey(
    *,
    company_id: str,
    company_name: str,
    industry: str | None,
    facts: dict[str, Any],
    events: list[dict[str, Any]] | None = None,
) -> CompanyJourney:
    stages = build_journey_stages(facts)
    return CompanyJourney(
        company_id=company_id,
        company_name=company_name,
        industry=industry,
        stages=stages,
        current_stage=current_stage_name(stages),
        pipeline_health=pipeline_health_view(stages),
        events=list(events or []),
    )
