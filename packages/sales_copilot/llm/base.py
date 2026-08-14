from __future__ import annotations

from typing import Protocol

from sales_copilot.models.types import LLMProviderName, LLMRequest, LLMResponse


class LLMProvider(Protocol):
    name: LLMProviderName

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a completion for the given request."""


class BaseLLMAdapter:
    name: LLMProviderName
    model: str

    def __init__(self, *, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or self.default_model()

    def default_model(self) -> str:
        raise NotImplementedError

    def available(self) -> bool:
        return bool(self.api_key)

    def complete(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError
