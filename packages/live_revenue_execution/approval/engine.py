from __future__ import annotations

from live_revenue_execution.models.types import ApprovalAction, ApprovalCard, LREInput, ProductionEmailPlan, WhatsAppPlan


class ApprovalCenterEngine:
    """Build founder approval cards before any live send."""

    def build_card(
        self,
        item: LREInput,
        *,
        email_plan: ProductionEmailPlan | None,
        whatsapp_plan: WhatsAppPlan | None,
    ) -> ApprovalCard:
        if item.campaign_id is None:
            raise ValueError("campaign_id required for approval card")
        dm = item.decision_makers[0] if item.decision_makers else {}
        risk = float(item.risk_score)
        if not item.to_email and not item.to_whatsapp:
            risk = max(risk, 70.0)
        if item.probability < 40:
            risk = max(risk, 55.0)
        action = ApprovalAction.APPROVE
        if risk >= 75:
            action = ApprovalAction.SEND_LATER
        elif item.probability < 35:
            action = ApprovalAction.EDIT
        return ApprovalCard(
            campaign_id=item.campaign_id,
            company_id=item.company_id,
            company_name=item.company_name,
            decision_maker=dm,
            pain_points=list(item.pain_points)[:8],
            evidence=list(item.evidence)[:20],
            email_preview=email_plan,
            whatsapp_preview=whatsapp_plan,
            attachments=list(item.attachments),
            calendly_preview=item.calendly_url,
            probability=float(item.probability),
            risk_score=round(risk, 4),
            priority=item.priority_grade or "B",
            recommended_action=action,
        )
