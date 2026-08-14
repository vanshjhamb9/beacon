from __future__ import annotations

from communication_gateway.calendar.calendly import CalendlyHooks
from communication_gateway.calendar.google_calendar import GoogleCalendarProvider
from communication_gateway.calendar.outlook import OutlookCalendarProvider
from communication_gateway.email.gmail import GmailProvider
from communication_gateway.email.microsoft_graph import MicrosoftGraphEmailProvider
from communication_gateway.models.types import (
    ChannelType,
    CommunicationMode,
    GatewayConfig,
    ProviderName,
)
from communication_gateway.sandbox.calendar import SandboxCalendarProvider
from communication_gateway.sandbox.email import SandboxEmailProvider
from communication_gateway.sandbox.whatsapp import SandboxWhatsAppProvider
from communication_gateway.whatsapp.meta import MetaWhatsAppProvider


class ProviderFactory:
    def __init__(self, config: GatewayConfig, *, access_tokens: dict[str, str] | None = None) -> None:
        self.config = config
        self.access_tokens = access_tokens or {}
        self.sandbox_email = SandboxEmailProvider()
        self.sandbox_whatsapp = SandboxWhatsAppProvider()
        self.sandbox_calendar = SandboxCalendarProvider()

    def email_provider(self, preferred: ProviderName | None = None):
        if self._force_sandbox():
            return self.sandbox_email
        provider = preferred or ProviderName.GMAIL
        token = self.access_tokens.get(provider.value) or self.access_tokens.get("email")
        if provider == ProviderName.MICROSOFT_GRAPH:
            return MicrosoftGraphEmailProvider(access_token=token or "")
        return GmailProvider(access_token=token or "", daily_quota=self.config.daily_email_quota)

    def whatsapp_provider(self, preferred: ProviderName | None = None):
        if self._force_sandbox():
            return self.sandbox_whatsapp
        return MetaWhatsAppProvider(
            access_token=self.config.meta_whatsapp_token or "",
            phone_number_id=self.config.meta_whatsapp_phone_number_id or "",
            app_secret=self.config.meta_whatsapp_app_secret,
            verify_token=self.config.meta_whatsapp_verify_token,
        )

    def calendar_provider(self, preferred: ProviderName | None = None):
        if self._force_sandbox():
            return self.sandbox_calendar
        provider = preferred or ProviderName.GOOGLE_CALENDAR
        token = self.access_tokens.get(provider.value) or self.access_tokens.get("calendar")
        if provider == ProviderName.OUTLOOK_CALENDAR:
            return OutlookCalendarProvider(access_token=token or "")
        if provider == ProviderName.CALENDLY:
            return CalendlyHooks(api_key=self.config.calendly_api_key)
        return GoogleCalendarProvider(access_token=token or "")

    def for_channel(self, channel: ChannelType):
        if channel == ChannelType.EMAIL:
            return self.email_provider()
        if channel == ChannelType.WHATSAPP:
            return self.whatsapp_provider()
        return self.calendar_provider()

    def _force_sandbox(self) -> bool:
        if self.config.mode == CommunicationMode.SANDBOX:
            return True
        if not self.config.allow_production_send:
            return True
        return False
