"""Execution readiness engine — Planning / Ready / Executing gate."""

from __future__ import annotations

from typing import Any

from execution_readiness.enums import ExecutionMode
from execution_readiness.models import DEFAULT_ORG_ID, VERSION, ExecutionStatusSnapshot, ProviderSnapshot
from execution_readiness.schemas import (
    ExecutionReadinessResponse,
    ExecutionStatusResponse,
    PlanningTargetCard,
    ValidateResponse,
)
from execution_readiness.validators import (
    build_checks,
    capabilities_for,
    derive_mode,
    missing_requirements,
    planning_target_card,
    recommendation_for,
    sanitize_next_step,
    truthful_kpi_contacted,
)


class ExecutionReadinessEngine:
    """Compose-only gate. Never invents delivery."""

    def evaluate(
        self,
        *,
        providers: list[ProviderSnapshot],
        verified_deliveries: int = 0,
        messages_sent: int = 0,
        organization_id: str = DEFAULT_ORG_ID,
    ) -> ExecutionStatusSnapshot:
        mode, reason = derive_mode(providers=providers, verified_deliveries=verified_deliveries)
        email_ready = any(
            p.connected and p.can_send and p.provider.value in {"gmail", "outlook", "graph", "sendgrid", "smtp"}
            for p in providers
        )
        whatsapp_ready = any(
            p.connected and p.can_send and p.provider.value == "meta_whatsapp" for p in providers
        )
        communication_ready = mode in {ExecutionMode.READY, ExecutionMode.EXECUTING}
        tracking_ready = mode == ExecutionMode.EXECUTING
        followup_ready = mode == ExecutionMode.EXECUTING
        checks = build_checks(providers=providers, verified_deliveries=verified_deliveries)
        caps = capabilities_for(mode)
        missing = missing_requirements(checks, mode)
        rec = recommendation_for(mode, email_ready=email_ready, whatsapp_ready=whatsapp_ready)

        return ExecutionStatusSnapshot(
            organization_id=organization_id,
            execution_mode=mode,
            reason=reason,
            communication_ready=communication_ready,
            email_ready=email_ready,
            whatsapp_ready=whatsapp_ready,
            tracking_ready=tracking_ready,
            followup_ready=followup_ready,
            providers=providers,
            capabilities=caps,
            missing_requirements=missing,
            recommendation=rec,
            messages_sent=messages_sent if mode != ExecutionMode.PLANNING else 0,
            deliveries=verified_deliveries if mode != ExecutionMode.PLANNING else 0,
            open_tracking="Enabled" if tracking_ready else "Disabled",
            reply_tracking="Enabled" if tracking_ready else "Disabled",
            learning_mode="Online" if mode == ExecutionMode.EXECUTING else "Offline",
            scoring_version=VERSION,
        )

    def status_response(self, snap: ExecutionStatusSnapshot) -> ExecutionStatusResponse:
        connected = [p.provider.value for p in snap.providers if p.connected]
        return ExecutionStatusResponse(
            current_mode=snap.execution_mode,
            connected_providers=connected,
            capabilities=snap.capabilities,
            recommendation=snap.recommendation,
            missing_requirements=snap.missing_requirements,
            email_ready=snap.email_ready,
            whatsapp_ready=snap.whatsapp_ready,
            tracking_ready=snap.tracking_ready,
            followup_ready=snap.followup_ready,
            communication_ready=snap.communication_ready,
            reason=snap.reason,
        )

    def readiness_response(self, snap: ExecutionStatusSnapshot) -> ExecutionReadinessResponse:
        checks = build_checks(providers=snap.providers, verified_deliveries=snap.deliveries)
        return ExecutionReadinessResponse(
            execution_mode=snap.execution_mode,
            reason=snap.reason,
            providers=snap.providers,
            checks=checks,
            capabilities=snap.capabilities,
            missing_requirements=snap.missing_requirements,
            recommendation=snap.recommendation,
            messages_sent=snap.messages_sent,
            deliveries=snap.deliveries,
            open_tracking=snap.open_tracking,
            reply_tracking=snap.reply_tracking,
            learning_mode=snap.learning_mode,
        )

    def validate_response(self, snap: ExecutionStatusSnapshot) -> ValidateResponse:
        checks = build_checks(providers=snap.providers, verified_deliveries=snap.deliveries)
        passed = snap.execution_mode in {ExecutionMode.READY, ExecutionMode.EXECUTING}
        return ValidateResponse(
            execution_mode=snap.execution_mode,
            passed=passed,
            checks=checks,
            recommendation=snap.recommendation,
        )

    def report_section(self, snap: ExecutionStatusSnapshot) -> dict[str, Any]:
        return {
            "mode": snap.execution_mode.value,
            "reason": snap.reason,
            "messages_sent": snap.messages_sent,
            "deliveries": snap.deliveries,
            "open_tracking": snap.open_tracking,
            "reply_tracking": snap.reply_tracking,
            "learning_mode": snap.learning_mode,
            "email_ready": snap.email_ready,
            "whatsapp_ready": snap.whatsapp_ready,
            "communication_ready": snap.communication_ready,
            "recommendation": snap.recommendation,
        }

    def planning_card(
        self,
        snap: ExecutionStatusSnapshot,
        *,
        company: str,
        email: str | None,
        why_now: str | None,
    ) -> PlanningTargetCard:
        return planning_target_card(
            company=company,
            email=email,
            why_now=why_now,
            reason=snap.reason,
        )

    def sanitize_next_step(self, step: str | None, snap: ExecutionStatusSnapshot) -> str:
        return sanitize_next_step(step, snap.execution_mode)

    def contacted_kpi(self, snap: ExecutionStatusSnapshot, verified_delivered_companies: int) -> int:
        return truthful_kpi_contacted(
            mode=snap.execution_mode,
            verified_delivered_companies=verified_delivered_companies,
        )
