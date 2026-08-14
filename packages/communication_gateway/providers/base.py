from __future__ import annotations

from typing import Protocol

from communication_gateway.models.types import (
    CalendarBookingResult,
    CalendarEventRequest,
    DeliveryResult,
    OutboundMessage,
    ProviderName,
)


class EmailProvider(Protocol):
    name: ProviderName

    def send(self, message: OutboundMessage) -> DeliveryResult: ...

    def create_draft(self, message: OutboundMessage) -> DeliveryResult: ...


class WhatsAppProvider(Protocol):
    name: ProviderName

    def send(self, message: OutboundMessage) -> DeliveryResult: ...


class CalendarProvider(Protocol):
    name: ProviderName

    def book(self, request: CalendarEventRequest) -> CalendarBookingResult: ...
