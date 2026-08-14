from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status

from app.api.dependencies import DatabaseDep, RedisDep, SettingsDep
from app.schemas.communication import (
    CampaignExecuteRequest,
    CampaignStopRequest,
    CommunicationModeResponse,
    ConversationItemResponse,
    E2EApproveSendReplyRequest,
    E2ERunResponse,
    FounderSendRequest,
    InboxThreadResponse,
    OAuthAuthorizeRequest,
    OAuthAuthorizeResponse,
    QueueHealthResponse,
    SandboxMeetingRequest,
    SandboxSendRequest,
    SystemHealthResponse,
    WebhookIngestResponse,
)
from app.services.communication import CommunicationPlatformService
from communication_gateway.models.types import ProviderName

router = APIRouter(tags=["communication-gateway"])


def get_communication_service(
    database: DatabaseDep, settings: SettingsDep
) -> CommunicationPlatformService:
    return CommunicationPlatformService(database, settings)


CommunicationServiceDep = Annotated[CommunicationPlatformService, Depends(get_communication_service)]


@router.get("/communication/mode", response_model=CommunicationModeResponse)
async def communication_mode(service: CommunicationServiceDep) -> CommunicationModeResponse:
    return CommunicationModeResponse.model_validate(await service.mode_status())


@router.get("/communication/queues", response_model=QueueHealthResponse)
async def communication_queues(service: CommunicationServiceDep) -> QueueHealthResponse:
    return QueueHealthResponse.model_validate(service.gateway.queue_health())


@router.post("/communication/queues/process")
async def process_communication_queue(
    service: CommunicationServiceDep,
    limit: int = Query(default=25, ge=1, le=200),
) -> dict[str, Any]:
    return await service.process_queue(limit=limit)


@router.post("/communication/sandbox/send")
async def sandbox_send(body: SandboxSendRequest, service: CommunicationServiceDep) -> dict[str, Any]:
    if not service.gateway.is_sandbox:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sandbox send requires COMMUNICATION_MODE=sandbox or ALLOW_PRODUCTION_SEND=false",
        )
    return await service.sandbox_send(body.model_dump())


@router.post("/communication/send")
async def founder_approved_send(body: FounderSendRequest, service: CommunicationServiceDep) -> dict[str, Any]:
    result = await service.founder_approved_send(body.model_dump())
    if result.get("error_code") == "approval_required":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result.get("error_message"))
    if result.get("error_code") == "oauth_required":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=result.get("error_message"))
    return result


@router.post("/communication/campaigns/{campaign_id}/execute")
async def execute_approved_campaign(
    campaign_id: UUID,
    body: CampaignExecuteRequest,
    service: CommunicationServiceDep,
) -> dict[str, Any]:
    result = await service.execute_approved_campaign(campaign_id, body.model_dump())
    if result.get("error_code") == "approval_required":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=result.get("error_message"))
    if result.get("error_code") == "campaign_not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return result


@router.get("/communication/oauth/status")
async def oauth_status(
    service: CommunicationServiceDep,
    provider: str = Query(default="gmail"),
) -> dict[str, Any]:
    return await service.oauth_status(provider)


@router.post("/communication/oauth/refresh")
async def oauth_refresh(service: CommunicationServiceDep) -> dict[str, Any]:
    return await service.refresh_oauth_tokens()


@router.post("/communication/sync/gmail-replies")
async def sync_gmail_replies(
    service: CommunicationServiceDep,
    max_messages: int = Query(default=20, ge=1, le=100),
) -> dict[str, Any]:
    return await service.sync_gmail_replies(max_messages=max_messages)


@router.post("/communication/e2e/approve-send-reply")
async def e2e_approve_send_reply(
    service: CommunicationServiceDep,
    body: E2EApproveSendReplyRequest | None = None,
) -> dict[str, Any]:
    return await service.e2e_approve_send_reply(body.model_dump() if body else {})


@router.post("/communication/sandbox/meeting")
async def sandbox_meeting(body: SandboxMeetingRequest, service: CommunicationServiceDep) -> dict[str, Any]:
    if not service.gateway.is_sandbox:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sandbox meeting requires sandbox mode")
    return await service.book_sandbox_meeting(body.model_dump())


@router.post("/communication/campaigns/{campaign_id}/stop")
async def stop_campaign(
    campaign_id: UUID,
    body: CampaignStopRequest,
    service: CommunicationServiceDep,
) -> dict[str, Any]:
    return await service.stop_campaign(campaign_id, reason=body.reason, actor=body.actor)


@router.post("/communication/oauth/authorize", response_model=OAuthAuthorizeResponse)
async def oauth_authorize(body: OAuthAuthorizeRequest, service: CommunicationServiceDep) -> OAuthAuthorizeResponse:
    try:
        data = await service.oauth_authorize_url(body.provider, state=body.state)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return OAuthAuthorizeResponse.model_validate(data)


@router.get("/communication/oauth/callback")
async def oauth_callback(
    service: CommunicationServiceDep,
    code: str = Query(...),
    state: str = Query(default="beacon"),
    provider: str = Query(default="gmail"),
) -> dict[str, Any]:
    try:
        bundle = service.oauth.exchange_code(ProviderName(provider), code=code)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    expires_in = None
    if bundle.expires_at is not None:
        from datetime import UTC, datetime

        expires_in = max(60, int((bundle.expires_at - datetime.now(UTC)).total_seconds()))
    stored = await service.oauth_store_tokens(
        provider,
        access_token=bundle.access_token,
        refresh_token=bundle.refresh_token,
        account_email=bundle.account_email,
        expires_in=expires_in,
        scopes=list(bundle.scopes or []),
    )
    return {"ok": True, "state": state, "connection": stored}


@router.get("/communication/webhooks/meta")
async def meta_webhook_verify(
    service: CommunicationServiceDep,
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> Response:
    expected = service.config.meta_whatsapp_verify_token
    if hub_mode == "subscribe" and expected and hub_verify_token == expected:
        return Response(content=hub_challenge or "", media_type="text/plain")
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Verification failed")


@router.post("/communication/webhooks/meta", response_model=WebhookIngestResponse)
async def meta_webhook_ingest(
    request: Request,
    service: CommunicationServiceDep,
    x_hub_signature_256: str | None = Header(default=None),
) -> WebhookIngestResponse:
    body = await request.body()
    signature_valid = False
    if service.config.meta_whatsapp_app_secret and x_hub_signature_256:
        from communication_gateway.security.crypto import hmac_sha256_hex

        expected = "sha256=" + hmac_sha256_hex(service.config.meta_whatsapp_app_secret, body)
        from communication_gateway.security.crypto import constant_time_compare

        signature_valid = constant_time_compare(expected, x_hub_signature_256)
    elif service.gateway.is_sandbox:
        signature_valid = True
    import json

    payload = json.loads(body.decode("utf-8") or "{}")
    result = await service.ingest_webhook("meta_whatsapp", payload, signature_valid=signature_valid)
    return WebhookIngestResponse.model_validate(result)


@router.post("/communication/webhooks/calendly", response_model=WebhookIngestResponse)
async def calendly_webhook_ingest(payload: dict[str, Any], service: CommunicationServiceDep) -> WebhookIngestResponse:
    result = await service.ingest_webhook("calendly", payload, signature_valid=True)
    return WebhookIngestResponse.model_validate(result)


@router.post("/communication/webhooks/gmail", response_model=WebhookIngestResponse)
async def gmail_webhook_ingest(payload: dict[str, Any], service: CommunicationServiceDep) -> WebhookIngestResponse:
    result = await service.ingest_webhook("gmail", payload, signature_valid=True)
    return WebhookIngestResponse.model_validate(result)


@router.get("/communication/metrics")
async def communication_metrics(service: CommunicationServiceDep) -> Response:
    return Response(content=service.prometheus_metrics(), media_type="text/plain; version=0.0.4")


@router.get("/inbox", response_model=list[InboxThreadResponse])
async def inbox(
    service: CommunicationServiceDep,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[InboxThreadResponse]:
    rows = await service.inbox(limit=limit)
    return [InboxThreadResponse.model_validate(row) for row in rows]


@router.get("/inbox/{conversation_id}", response_model=list[ConversationItemResponse])
async def inbox_conversation(
    conversation_id: UUID,
    service: CommunicationServiceDep,
) -> list[ConversationItemResponse]:
    rows = await service.conversation_timeline(conversation_id)
    return [ConversationItemResponse.model_validate(row) for row in rows]


@router.get("/qa/health", response_model=SystemHealthResponse)
async def qa_health(service: CommunicationServiceDep, redis: RedisDep) -> SystemHealthResponse:
    report = await service.system_health(redis)
    return SystemHealthResponse.model_validate(report)


@router.get("/system-health", response_model=SystemHealthResponse)
async def system_health(service: CommunicationServiceDep, redis: RedisDep) -> SystemHealthResponse:
    report = await service.system_health(redis)
    return SystemHealthResponse.model_validate(report)


@router.post("/qa/e2e/sandbox", response_model=E2ERunResponse)
async def run_sandbox_e2e(service: CommunicationServiceDep) -> E2ERunResponse:
    result = await service.run_e2e()
    return E2ERunResponse.model_validate(result)


@router.get("/qa/dashboard", response_model=SystemHealthResponse)
async def qa_dashboard(service: CommunicationServiceDep, redis: RedisDep) -> SystemHealthResponse:
    report = await service.system_health(redis)
    return SystemHealthResponse.model_validate(report)
