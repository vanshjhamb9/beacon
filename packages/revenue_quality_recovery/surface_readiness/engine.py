from __future__ import annotations

from typing import Any

from revenue_quality_recovery.models.types import (
    CompanyProfile,
    RevenueVerdict,
    SalesReadyGateResult,
    SurfaceAdmission,
    SurfaceStatus,
    UNKNOWN,
)

ALLOWED_STATUSES = frozenset(
    {
        SurfaceStatus.CONTACT_READY.value,
        SurfaceStatus.SALES_READY.value,
        SurfaceStatus.ENTERPRISE_READY.value,
    }
)

SURFACES = ("Founder Queue", "Revenue Hunter", "Campaigns", "Email", "WhatsApp")


class SurfaceReadinessEngine:
    """Rule 9 — only CONTACT/SALES/ENTERPRISE READY enter founder/revenue surfaces. Everything else hidden."""

    def admit(
        self,
        *,
        gate: SalesReadyGateResult,
        profile: CompanyProfile | None,
        payload: dict[str, Any] | None = None,
    ) -> SurfaceAdmission:
        payload = payload or {}
        # Map binary gate to surface status
        if gate.verdict == RevenueVerdict.SALES_READY and profile and profile.sales_ready_badge:
            employees = payload.get("employees") or payload.get("employee_estimate") or 0
            try:
                emp = int(employees)
            except (TypeError, ValueError):
                emp = 0
            if emp >= 500 or str(payload.get("segment") or "").lower() == "enterprise":
                status = SurfaceStatus.ENTERPRISE_READY.value
            else:
                status = SurfaceStatus.SALES_READY.value
            # CONTACT READY if sales ready but thinner contact set
            if profile.verified_emails or profile.verified_phones or profile.decision_makers:
                pass
            else:
                status = SurfaceStatus.CONTACT_READY.value

            return SurfaceAdmission(
                admitted=True,
                status=status,
                surfaces=list(SURFACES),
                hidden=False,
                evidence=[f"admitted:{status}", *[f"surface:{s}" for s in SURFACES]],
            )

        # Explicit status override only if already in allowed set AND gate passed
        explicit = str(payload.get("surface_status") or payload.get("status") or "")
        if gate.verdict == RevenueVerdict.SALES_READY and explicit in ALLOWED_STATUSES:
            return SurfaceAdmission(
                admitted=True,
                status=explicit,
                surfaces=list(SURFACES),
                hidden=False,
                evidence=[f"admitted:{explicit}"],
            )

        return SurfaceAdmission(
            admitted=False,
            status=UNKNOWN,
            surfaces=[],
            hidden=True,
            evidence=["hidden:not_sales_ready", f"gate:{gate.verdict.value}"],
        )
