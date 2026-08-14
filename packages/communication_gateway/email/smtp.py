"""
SMTP Email Provider for Beacon
Handles email sending via SMTP protocol.
"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Any, Optional

from ..models.types import (
    DeliveryResult,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)


class SMTPEmailProvider:
    """SMTP email sender provider."""

    name = ProviderName.SMTP

    def __init__(
        self,
        host: str,
        port: int = 587,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True,
        from_address: Optional[str] = None,
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.from_address = from_address

    def _build_mime_message(self, message: OutboundMessage) -> MIMEMultipart:
        """Build MIME message from OutboundMessage."""
        msg = MIMEMultipart("alternative")
        msg["From"] = message.from_address or self.from_address
        msg["To"] = message.to_address
        msg["Subject"] = message.subject or ""

        # Add tracking headers
        if message.campaign_id:
            msg["X-Beacon-Campaign-Id"] = str(message.campaign_id)
        if message.opportunity_id:
            msg["X-Beacon-Opportunity-Id"] = str(message.opportunity_id)

        # Add text body
        if message.body_text:
            text_part = MIMEText(message.body_text, "plain")
            msg.attach(text_part)

        # Add HTML body if provided
        if message.body_html:
            html_part = MIMEText(message.body_html, "html")
            msg.attach(html_part)

        return msg

    def send(self, message: OutboundMessage) -> DeliveryResult:
        """Send email via SMTP."""
        try:
            mime_msg = self._build_mime_message(message)

            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP_SSL(self.host, self.port)
            else:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()

            # Authenticate if credentials provided
            if self.username and self.password:
                server.login(self.username, self.password)

            # Send email
            from_addr = message.from_address or self.from_address
            to_addr = message.to_address

            server.sendmail(from_addr, [to_addr], mime_msg.as_string())
            server.quit()

            return DeliveryResult(
                state=DeliveryState.SENT,
                provider=ProviderName.SMTP,
                provider_message_id=f"smtp_{datetime.now().timestamp()}",
                sandbox=False,
                raw={
                    "host": self.host,
                    "port": self.port,
                    "from": from_addr,
                    "to": to_addr,
                },
            )

        except smtplib.SMTPAuthenticationError as e:
            return DeliveryResult(
                state=DeliveryState.FAILED,
                provider=ProviderName.SMTP,
                error_code="AUTH_ERROR",
                error_message=str(e),
            )
        except smtplib.SMTPRecipientsRefused as e:
            return DeliveryResult(
                state=DeliveryState.FAILED,
                provider=ProviderName.SMTP,
                error_code="RECIPIENTS_REFUSED",
                error_message=str(e),
            )
        except Exception as e:
            return DeliveryResult(
                state=DeliveryState.FAILED,
                provider=ProviderName.SMTP,
                error_code="EXCEPTION",
                error_message=str(e),
            )

    def create_draft(self, message: OutboundMessage) -> DeliveryResult:
        """SMTP doesn't support drafts, return success for compatibility."""
        return DeliveryResult(
            state=DeliveryState.DRAFT,
            provider=ProviderName.SMTP,
            sandbox=False,
            raw={"note": "SMTP does not support drafts"},
        )


class SandboxSMTPEmailProvider:
    """Sandbox SMTP provider for testing."""

    name = ProviderName.SANDBOX_EMAIL

    def __init__(self):
        self.sent_messages: list[dict] = []

    def send(self, message: OutboundMessage) -> DeliveryResult:
        """Simulate sending an email."""
        self.sent_messages.append({
            "from": message.from_address,
            "to": message.to_address,
            "subject": message.subject,
            "body": message.body_text,
            "timestamp": datetime.now().isoformat(),
        })

        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=ProviderName.SANDBOX_EMAIL,
            provider_message_id=f"sandbox_{len(self.sent_messages)}",
            sandbox=True,
            raw={"simulated": True},
        )

    def create_draft(self, message: OutboundMessage) -> DeliveryResult:
        """Simulate creating an email draft."""
        return DeliveryResult(
            state=DeliveryState.DRAFT,
            provider=ProviderName.SANDBOX_EMAIL,
            sandbox=True,
            raw={"simulated": True},
        )
