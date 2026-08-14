"""
Reddit OAuth Provider for Beacon
Handles Reddit OAuth 2.0 authentication and DM sending.
"""
import base64
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx

from ..models.types import (
    DeliveryResult,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)


class RedditOAuth:
    """Reddit OAuth 2.0 flow handler."""

    AUTH_URL = "https://www.reddit.com/api/v1/authorize"
    TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
    SCOPES = ["identity", "read", "submit", "privatemessages"]

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str, user_agent: str = "BeaconOutreach/1.0"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.user_agent = user_agent

    def get_authorization_url(self, state: str = "beacon_outreach") -> str:
        """Generate Reddit OAuth authorization URL."""
        scopes = "+".join(self.SCOPES)
        return (
            f"{self.AUTH_URL}"
            f"?client_id={self.client_id}"
            f"&response_type=code"
            f"&state={state}"
            f"&redirect_uri={self.redirect_uri}"
            f"&duration=permanent"
            f"&scope={scopes}"
        )

    async def exchange_code(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access token."""
        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "User-Agent": self.user_agent,
                },
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                },
            )
            response.raise_for_status()
            return response.json()

    async def refresh_token(self, refresh_token: str) -> dict[str, Any]:
        """Refresh access token."""
        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.TOKEN_URL,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "User-Agent": self.user_agent,
                },
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
            response.raise_for_status()
            return response.json()


class RedditProvider:
    """Reddit DM sender provider."""

    name = ProviderName.REDDIT
    BASE_URL = "https://oauth.reddit.com"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        user_agent: str = "BeaconOutreach/1.0",
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.user_agent = user_agent
        self.token_expires_at: Optional[datetime] = None

    def _headers(self) -> dict[str, str]:
        """Build request headers."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "User-Agent": self.user_agent,
            "Content-Type": "application/x-www-form-urlencoded",
        }

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        """Send a Reddit DM."""
        try:
            # Reddit uses POST /api/send for DMs
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/api/send",
                    headers=self._headers(),
                    data={
                        "to": message.to_address,
                        "subject": message.subject or "Message from Inowix",
                        "text": message.body_text,
                    },
                )

                if response.status_code == 200:
                    return DeliveryResult(
                        state=DeliveryState.SENT,
                        provider=ProviderName.REDDIT,
                        provider_message_id=response.json().get("id"),
                        sandbox=False,
                        raw=response.json(),
                    )
                else:
                    return DeliveryResult(
                        state=DeliveryState.FAILED,
                        provider=ProviderName.REDDIT,
                        error_code=str(response.status_code),
                        error_message=response.text,
                        raw={"status_code": response.status_code},
                    )

        except Exception as e:
            return DeliveryResult(
                state=DeliveryState.FAILED,
                provider=ProviderName.REDDIT,
                error_code="EXCEPTION",
                error_message=str(e),
            )

    async def get_inbox(self, limit: int = 25) -> list[dict[str, Any]]:
        """Get Reddit inbox messages."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/message/inbox",
                    headers=self._headers(),
                    params={"limit": limit},
                )
                response.raise_for_status()
                data = response.json()
                return data.get("data", {}).get("children", [])
        except Exception:
            return []

    async def reply_to_message(self, message_id: str, text: str) -> DeliveryResult:
        """Reply to a Reddit message."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/api/comment",
                    headers=self._headers(),
                    data={
                        "thing_id": message_id,
                        "text": text,
                    },
                )

                if response.status_code == 200:
                    return DeliveryResult(
                        state=DeliveryState.SENT,
                        provider=ProviderName.REDDIT,
                        provider_message_id=response.json().get("id"),
                        sandbox=False,
                        raw=response.json(),
                    )
                else:
                    return DeliveryResult(
                        state=DeliveryState.FAILED,
                        provider=ProviderName.REDDIT,
                        error_code=str(response.status_code),
                        error_message=response.text,
                    )
        except Exception as e:
            return DeliveryResult(
                state=DeliveryState.FAILED,
                provider=ProviderName.REDDIT,
                error_code="EXCEPTION",
                error_message=str(e),
            )


class SandboxRedditProvider:
    """Sandbox Reddit provider for testing."""

    name = ProviderName.SANDBOX_REDDIT

    def __init__(self):
        self.sent_messages: list[dict] = []

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        """Simulate sending a Reddit DM."""
        self.sent_messages.append({
            "to": message.to_address,
            "subject": message.subject,
            "body": message.body_text,
            "timestamp": datetime.now().isoformat(),
        })

        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=ProviderName.SANDBOX_REDDIT,
            provider_message_id=f"sandbox_{len(self.sent_messages)}",
            sandbox=True,
            raw={"simulated": True},
        )
