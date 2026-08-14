"""Pure validators — decide mode from provider + delivery facts. No GPT."""

from __future__ import annotations

from execution_readiness.enums import (
    EXECUTING_ALLOWED,
    FORBIDDEN_NEXT_STEP_PHRASES,
    PLANNING_ALLOWED,
    READY_ALLOWED,
    Capability,
    ExecutionMode,
)
from execution_readiness.models import ProviderSnapshot, ReadinessCheck
from execution_readiness.schemas import PlanningTargetCard


def derive_mode(
    *,
    providers: list[ProviderSnapshot],
    verified_deliveries: int,
) -> tuple[ExecutionMode, str]:
    email_ready = any(
        p.connected and p.oauth_valid and p.can_send and p.provider.value in {"gmail", "outlook", "graph", "sendgrid", "smtp"}
        for p in providers
    )
    whatsapp_ready = any(
        p.connected and p.can_send and p.provider.value == "meta_whatsapp" for p in providers
    )
    # READY requires provider + oauth valid (+ webhook when email)
    ready = False
    for p in providers:
        if not (p.connected and p.can_send):
            continue
        if p.provider.value == "meta_whatsapp":
            ready = True
            break
        if p.oauth_valid and p.webhook_verified:
            ready = True
            break
        # OAuth valid without webhook still READY for test send (strict READY wants webhook)
        if p.oauth_valid:
            ready = True
            break

    if verified_deliveries > 0 and (email_ready or whatsapp_ready or ready):
        return ExecutionMode.EXECUTING, "At least one verified provider delivery exists."
    if ready:
        return ExecutionMode.READY, "Provider connected with valid credentials; awaiting first verified delivery."
    return ExecutionMode.PLANNING, "No verified communication provider connected."


def capabilities_for(mode: ExecutionMode) -> list[str]:
    mapping = {
        ExecutionMode.PLANNING: PLANNING_ALLOWED,
        ExecutionMode.READY: READY_ALLOWED,
        ExecutionMode.EXECUTING: EXECUTING_ALLOWED,
    }
    return sorted(c.value for c in mapping[mode])


def allows(mode: ExecutionMode, capability: Capability | str) -> bool:
    cap = capability if isinstance(capability, Capability) else Capability(str(capability))
    return cap.value in set(capabilities_for(mode))


def build_checks(
    *,
    providers: list[ProviderSnapshot],
    verified_deliveries: int,
) -> list[ReadinessCheck]:
    email = next((p for p in providers if p.provider.value in {"gmail", "outlook", "graph"}), None)
    wa = next((p for p in providers if p.provider.value == "meta_whatsapp"), None)
    return [
        ReadinessCheck(
            name="email_provider_connected",
            passed=bool(email and email.connected),
            detail=(email.detail if email else "No email provider"),
        ),
        ReadinessCheck(
            name="email_oauth_valid",
            passed=bool(email and email.oauth_valid),
            detail="OAuth active" if email and email.oauth_valid else "OAuth missing/invalid",
        ),
        ReadinessCheck(
            name="email_webhook_verified",
            passed=bool(email and email.webhook_verified),
            detail="Webhook verified" if email and email.webhook_verified else "Webhook not verified",
        ),
        ReadinessCheck(
            name="email_can_send",
            passed=bool(email and email.can_send),
            detail="Can send" if email and email.can_send else "Cannot send",
        ),
        ReadinessCheck(
            name="whatsapp_connected",
            passed=bool(wa and wa.connected),
            detail=(wa.detail if wa else "Meta WhatsApp not configured"),
        ),
        ReadinessCheck(
            name="verified_deliveries",
            passed=verified_deliveries > 0,
            detail=f"{verified_deliveries} verified deliveries",
        ),
    ]


def missing_requirements(checks: list[ReadinessCheck], mode: ExecutionMode) -> list[str]:
    if mode == ExecutionMode.EXECUTING:
        return []
    missing = [c.name for c in checks if not c.passed]
    if mode == ExecutionMode.READY:
        return [m for m in missing if m == "verified_deliveries"] or ["verified_deliveries"]
    return missing


def recommendation_for(mode: ExecutionMode, *, email_ready: bool, whatsapp_ready: bool) -> str:
    if mode == ExecutionMode.EXECUTING:
        return "Execution active — tracking and learning use verified delivery events only."
    if mode == ExecutionMode.READY:
        return "Approve a draft and send a test message to enter Executing mode."
    if not email_ready and not whatsapp_ready:
        return "Connect Gmail to begin outreach."
    return "Complete OAuth / webhook verification to reach Ready mode."


def planning_target_card(
    *,
    company: str,
    email: str | None,
    why_now: str | None,
    reason: str,
) -> PlanningTargetCard:
    return PlanningTargetCard(
        company=company,
        status="READY TO SEND",
        reason=reason,
        next_action="Connect Gmail or Meta WhatsApp Business.",
        tracking="Disabled until first successful delivery.",
        email=email,
        why_now=why_now,
    )


def sanitize_next_step(step: str | None, mode: ExecutionMode) -> str:
    text = (step or "").strip()
    if mode == ExecutionMode.EXECUTING:
        return text or "Continue outreach based on verified outcomes"
    if mode == ExecutionMode.READY:
        if any(p in text.lower() for p in FORBIDDEN_NEXT_STEP_PHRASES):
            return "Approve draft and send via connected provider"
        return text or "Approve draft and send via connected provider"
    # PLANNING — never mention opens / follow-ups / reply tracking
    if not text or any(p in text.lower() for p in FORBIDDEN_NEXT_STEP_PHRASES):
        return "Connect Gmail or Meta WhatsApp Business."
    if text.lower().startswith("send first"):
        return "Connect a communication provider, then send the first outreach email."
    return text


def truthful_kpi_contacted(*, mode: ExecutionMode, verified_delivered_companies: int) -> int:
    if mode == ExecutionMode.PLANNING:
        return 0
    if not allows(mode, Capability.COUNT_CONTACTED):
        return 0
    return verified_delivered_companies
