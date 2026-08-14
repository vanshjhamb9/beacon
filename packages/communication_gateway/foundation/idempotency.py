from __future__ import annotations

"""Sprint 18A foundation helpers — compose-only send/reply path utilities."""

from hashlib import sha256
from typing import Any
from uuid import UUID


def build_idempotency_key(
    *,
    campaign_id: UUID | None,
    campaign_step_id: UUID | None,
    to_address: str,
    subject: str | None,
) -> str:
    raw = f"{campaign_id}:{campaign_step_id}:{to_address.lower().strip()}:{subject or ''}"
    return sha256(raw.encode("utf-8")).hexdigest()


def webhook_fingerprint(provider: str, payload: dict[str, Any]) -> str:
    hint = (
        str(payload.get("messageId") or "")
        or str(payload.get("historyId") or "")
        or str((payload.get("message") or {}).get("data") or "")
        or str(payload.get("id") or "")
    )
    if not hint:
        hint = sha256(str(sorted(payload.items())).encode("utf-8")).hexdigest()[:24]
    return f"{provider}:{hint}"
