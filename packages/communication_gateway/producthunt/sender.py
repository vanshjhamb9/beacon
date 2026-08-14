"""
Product Hunt Provider for Beacon
Handles Product Hunt API interactions.
"""
from datetime import datetime
from typing import Any, Optional

import httpx

from ..models.types import (
    DeliveryResult,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)


class ProductHuntProvider:
    """Product Hunt sender provider."""

    name = ProviderName.PRODUCTHUNT
    BASE_URL = "https://api.producthunt.com/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        """Send a message on Product Hunt."""
        # Product Hunt doesn't have a direct messaging API
        # This would need to be implemented via their GraphQL API
        # or via browser automation if they add messaging

        return DeliveryResult(
            state=DeliveryState.FAILED,
            provider=ProviderName.PRODUCTHUNT,
            error_code="NOT_SUPPORTED",
            error_message="Product Hunt does not currently support direct messaging via API",
        )

    async def get_user(self, username: str) -> Optional[dict[str, Any]]:
        """Get user profile from Product Hunt."""
        query = """
        query {
            user(username: "%s") {
                id
                name
                username
                headline
                website
                profileImage
            }
        }
        """ % username

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/graphql",
                    headers=self._headers(),
                    json={"query": query},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", {}).get("user")
        except Exception:
            return None


class SandboxProductHuntProvider:
    """Sandbox Product Hunt provider for testing."""

    name = ProviderName.SANDBOX_PRODUCTHUNT

    def __init__(self):
        self.sent_messages: list[dict] = []

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        """Simulate sending a Product Hunt message."""
        self.sent_messages.append({
            "to": message.to_address,
            "body": message.body_text,
            "timestamp": datetime.now().isoformat(),
        })

        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=ProviderName.SANDBOX_PRODUCTHUNT,
            provider_message_id=f"sandbox_{len(self.sent_messages)}",
            sandbox=True,
            raw={"simulated": True},
        )
