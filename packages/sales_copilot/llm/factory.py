from __future__ import annotations

from dataclasses import dataclass

from sales_copilot.llm.anthropic_adapter import AnthropicAdapter
from sales_copilot.llm.base import BaseLLMAdapter
from sales_copilot.llm.gemini_adapter import GeminiAdapter
from sales_copilot.llm.grounded import GroundedProvider
from sales_copilot.llm.openai_adapter import OpenAIAdapter
from sales_copilot.llm.openrouter_adapter import OpenRouterAdapter
from sales_copilot.models.types import LLMProviderName


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: LLMProviderName = LLMProviderName.GROUNDED
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    gemini_api_key: str | None = None
    openrouter_api_key: str | None = None
    openai_model: str | None = None
    anthropic_model: str | None = None
    gemini_model: str | None = None
    openrouter_model: str | None = None
    temperature: float = 0.2


class LLMProviderFactory:
    """Configuration-driven provider factory. No provider logic outside adapters."""

    def __init__(self, config: LLMProviderConfig | None = None) -> None:
        self.config = config or LLMProviderConfig()

    def create(self, preferred: LLMProviderName | None = None) -> BaseLLMAdapter:
        provider = preferred or self.config.provider
        adapter = self._build(provider)
        if adapter.available():
            return adapter
        # Fall back to grounded deterministic generation when keys are missing.
        return GroundedProvider(model="grounded-v1")

    def _build(self, provider: LLMProviderName) -> BaseLLMAdapter:
        if provider == LLMProviderName.OPENAI:
            return OpenAIAdapter(api_key=self.config.openai_api_key, model=self.config.openai_model)
        if provider == LLMProviderName.ANTHROPIC:
            return AnthropicAdapter(api_key=self.config.anthropic_api_key, model=self.config.anthropic_model)
        if provider == LLMProviderName.GEMINI:
            return GeminiAdapter(api_key=self.config.gemini_api_key, model=self.config.gemini_model)
        if provider == LLMProviderName.OPENROUTER:
            return OpenRouterAdapter(api_key=self.config.openrouter_api_key, model=self.config.openrouter_model)
        return GroundedProvider(model="grounded-v1")
