"""
IndieHackers DM Sender for Beacon
Uses Playwright for browser automation to send DMs.
"""
import asyncio
from datetime import datetime
from typing import Any, Optional

from ..models.types import (
    DeliveryResult,
    DeliveryState,
    OutboundMessage,
    ProviderName,
)


class IndieHackersSender:
    """IndieHackers DM sender using Playwright."""

    name = ProviderName.INDIEHACKERS
    BASE_URL = "https://www.indiehackers.com"

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        self.username = username
        self.password = password
        self.browser = None
        self.context = None
        self.page = None
        self._logged_in = False

    async def _ensure_browser(self):
        """Ensure Playwright browser is running."""
        if self.browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self.browser = await self._playwright.chromium.launch(headless=True)
                self.context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                self.page = await self.context.new_page()
            except ImportError:
                raise RuntimeError("Playwright not installed. Run: pip install playwright && playwright install")

    async def _login(self):
        """Login to IndieHackers."""
        if self._logged_in:
            return

        await self._ensure_browser()

        if not self.username or not self.password:
            raise RuntimeError("IndieHackers credentials not configured")

        try:
            await self.page.goto(f"{self.BASE_URL}/login")
            await self.page.wait_for_load_state("networkidle")

            # Fill login form
            await self.page.fill('input[name="email"]', self.username)
            await self.page.fill('input[name="password"]', self.password)
            await self.page.click('button[type="submit"]')

            # Wait for login
            await self.page.wait_for_url(f"{self.BASE_URL}/**", timeout=10000)
            self._logged_in = True
        except Exception as e:
            raise RuntimeError(f"IndieHackers login failed: {e}")

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        """Send a DM on IndieHackers."""
        try:
            await self._login()

            # Navigate to user profile
            # message.to_address should be the username
            profile_url = f"{self.BASE_URL}/@{message.to_address}"
            await self.page.goto(profile_url)
            await self.page.wait_for_load_state("networkidle")

            # Click message button
            message_button = await self.page.query_selector('a[href*="/messages/new"]')
            if not message_button:
                # Try alternative selector
                message_button = await self.page.query_selector('button:has-text("Message")')

            if message_button:
                await message_button.click()
                await self.page.wait_for_load_state("networkidle")

                # Fill message form
                message_input = await self.page.query_selector('textarea[name="body"]')
                if message_input:
                    await message_input.fill(message.body_text)

                    # Send message
                    send_button = await self.page.query_selector('button[type="submit"]')
                    if send_button:
                        await send_button.click()
                        await self.page.wait_for_load_state("networkidle")

                        return DeliveryResult(
                            state=DeliveryState.SENT,
                            provider=ProviderName.INDIEHACKERS,
                            provider_message_id=f"ih_{datetime.now().timestamp()}",
                            sandbox=False,
                            raw={"profile_url": profile_url},
                        )

            return DeliveryResult(
                state=DeliveryState.FAILED,
                provider=ProviderName.INDIEHACKERS,
                error_code="UI_NOT_FOUND",
                error_message="Could not find message UI elements",
            )

        except Exception as e:
            return DeliveryResult(
                state=DeliveryState.FAILED,
                provider=ProviderName.INDIEHACKERS,
                error_code="EXCEPTION",
                error_message=str(e),
            )

    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        if hasattr(self, '_playwright') and self._playwright:
            await self._playwright.stop()


class SandboxIndieHackersSender:
    """Sandbox IndieHackers sender for testing."""

    name = ProviderName.SANDBOX_INDIEHACKERS

    def __init__(self):
        self.sent_messages: list[dict] = []

    async def send(self, message: OutboundMessage) -> DeliveryResult:
        """Simulate sending an IndieHackers DM."""
        self.sent_messages.append({
            "to": message.to_address,
            "body": message.body_text,
            "timestamp": datetime.now().isoformat(),
        })

        return DeliveryResult(
            state=DeliveryState.SENT,
            provider=ProviderName.SANDBOX_INDIEHACKERS,
            provider_message_id=f"sandbox_{len(self.sent_messages)}",
            sandbox=True,
            raw={"simulated": True},
        )
