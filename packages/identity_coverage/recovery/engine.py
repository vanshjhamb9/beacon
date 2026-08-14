"""Identity recovery queue — nothing discarded forever."""

from __future__ import annotations

from typing import Any

from identity_coverage.models.types import RecoveryItem, RecoveryReason


class RecoveryQueueEngine:
    def enqueue_from_payload(self, payload: dict[str, Any], *, ranked: dict[str, Any] | None = None) -> list[RecoveryItem]:
        ranked = ranked or {}
        items: list[RecoveryItem] = []
        signal_id = str(payload.get("signal_id") or payload.get("id") or "unknown")
        domain = None
        if hasattr(ranked.get("official_domain"), "value"):
            domain = ranked["official_domain"].value
        domain = domain or payload.get("official_domain") or (payload.get("metadata") or {}).get("official_domain")

        website = ranked.get("website")
        has_website = bool(getattr(website, "value", None) if website else payload.get("official_website"))
        if not has_website:
            items.append(
                RecoveryItem(
                    signal_id=signal_id,
                    reason=RecoveryReason.WEBSITE_MISSING,
                    domain=domain,
                    payload={"source": payload.get("source")},
                )
            )
        if str(payload.get("source") or "") == "github_trending" and not has_website:
            items.append(
                RecoveryItem(
                    signal_id=signal_id,
                    reason=RecoveryReason.HOMEPAGE_MISSING,
                    domain=domain,
                    payload={"source": "github_trending"},
                )
            )
        email = ranked.get("business_email")
        if has_website and not getattr(email, "value", None):
            items.append(
                RecoveryItem(
                    signal_id=signal_id,
                    reason=RecoveryReason.NO_CONTACT,
                    domain=domain,
                    payload={},
                )
            )
        dm = ranked.get("decision_maker")
        if has_website and not getattr(dm, "value", None):
            items.append(
                RecoveryItem(
                    signal_id=signal_id,
                    reason=RecoveryReason.NO_DECISION_MAKER,
                    domain=domain,
                    payload={},
                )
            )
        conf = float(payload.get("confidence") or 0)
        if has_website and conf and conf < 50:
            items.append(
                RecoveryItem(
                    signal_id=signal_id,
                    reason=RecoveryReason.LOW_CONFIDENCE,
                    domain=domain,
                    payload={"confidence": conf},
                )
            )
        return items
