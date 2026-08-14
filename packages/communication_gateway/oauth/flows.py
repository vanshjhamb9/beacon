from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from communication_gateway.models.types import GatewayConfig, OAuthTokenBundle, ProviderName


class OAuthFlowService:
    """Configuration-driven OAuth 2.0 authorization code + refresh flows."""

    GOOGLE_AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN = "https://oauth2.googleapis.com/token"
    MICROSOFT_AUTH = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
    MICROSOFT_TOKEN = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"

    def __init__(self, config: GatewayConfig) -> None:
        self.config = config

    def authorize_url(self, provider: ProviderName, *, state: str, scopes: list[str] | None = None) -> str:
        if provider in {ProviderName.GMAIL, ProviderName.GOOGLE_CALENDAR}:
            scope = " ".join(
                scopes
                or [
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/gmail.modify",
                    "https://www.googleapis.com/auth/calendar.events",
                    "openid",
                    "email",
                ]
            )
            params = {
                "client_id": self.config.gmail_client_id or "",
                "redirect_uri": self.config.oauth_redirect_uri,
                "response_type": "code",
                "access_type": "offline",
                "prompt": "consent",
                "scope": scope,
                "state": state,
            }
            return f"{self.GOOGLE_AUTH}?{urlencode(params)}"
        if provider in {ProviderName.MICROSOFT_GRAPH, ProviderName.OUTLOOK_CALENDAR}:
            scope = " ".join(
                scopes
                or [
                    "offline_access",
                    "openid",
                    "email",
                    "https://graph.microsoft.com/Mail.Send",
                    "https://graph.microsoft.com/Mail.ReadWrite",
                    "https://graph.microsoft.com/Calendars.ReadWrite",
                ]
            )
            auth = self.MICROSOFT_AUTH.format(tenant=self.config.microsoft_tenant_id)
            params = {
                "client_id": self.config.microsoft_client_id or "",
                "redirect_uri": self.config.oauth_redirect_uri,
                "response_type": "code",
                "response_mode": "query",
                "scope": scope,
                "state": state,
            }
            return f"{auth}?{urlencode(params)}"
        raise ValueError(f"OAuth not supported for provider {provider.value}")

    def exchange_code(self, provider: ProviderName, *, code: str) -> OAuthTokenBundle:
        if provider in {ProviderName.GMAIL, ProviderName.GOOGLE_CALENDAR}:
            data = self._post(
                self.GOOGLE_TOKEN,
                {
                    "code": code,
                    "client_id": self.config.gmail_client_id or "",
                    "client_secret": self.config.gmail_client_secret or "",
                    "redirect_uri": self.config.oauth_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            return self._bundle(provider, data)
        if provider in {ProviderName.MICROSOFT_GRAPH, ProviderName.OUTLOOK_CALENDAR}:
            token_url = self.MICROSOFT_TOKEN.format(tenant=self.config.microsoft_tenant_id)
            data = self._post(
                token_url,
                {
                    "code": code,
                    "client_id": self.config.microsoft_client_id or "",
                    "client_secret": self.config.microsoft_client_secret or "",
                    "redirect_uri": self.config.oauth_redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            return self._bundle(provider, data)
        raise ValueError(f"OAuth not supported for provider {provider.value}")

    def refresh(self, provider: ProviderName, *, refresh_token: str) -> OAuthTokenBundle:
        if provider in {ProviderName.GMAIL, ProviderName.GOOGLE_CALENDAR}:
            data = self._post(
                self.GOOGLE_TOKEN,
                {
                    "client_id": self.config.gmail_client_id or "",
                    "client_secret": self.config.gmail_client_secret or "",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            data.setdefault("refresh_token", refresh_token)
            return self._bundle(provider, data)
        if provider in {ProviderName.MICROSOFT_GRAPH, ProviderName.OUTLOOK_CALENDAR}:
            token_url = self.MICROSOFT_TOKEN.format(tenant=self.config.microsoft_tenant_id)
            data = self._post(
                token_url,
                {
                    "client_id": self.config.microsoft_client_id or "",
                    "client_secret": self.config.microsoft_client_secret or "",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            data.setdefault("refresh_token", refresh_token)
            return self._bundle(provider, data)
        raise ValueError(f"Refresh not supported for provider {provider.value}")

    def _bundle(self, provider: ProviderName, data: dict[str, Any]) -> OAuthTokenBundle:
        expires_in = int(data.get("expires_in") or 3600)
        return OAuthTokenBundle(
            provider=provider,
            access_token=str(data.get("access_token") or ""),
            refresh_token=data.get("refresh_token"),
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            scopes=str(data.get("scope") or "").split(),
            metadata={"token_type": data.get("token_type")},
        )

    def _post(self, url: str, data: dict[str, str]) -> dict[str, Any]:
        with httpx.Client(timeout=45.0) as client:
            response = client.post(url, data=data)
            response.raise_for_status()
            return response.json()
