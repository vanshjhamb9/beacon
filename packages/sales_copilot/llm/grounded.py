from __future__ import annotations

import time

from sales_copilot.llm.base import BaseLLMAdapter
from sales_copilot.models.types import LLMProviderName, LLMRequest, LLMResponse


class GroundedProvider(BaseLLMAdapter):
    """Deterministic provider that echoes structured grounded content.

    Used when no external LLM key is configured. Generation logic lives in
    the grounded generator; this adapter records metadata only.
    """

    name = LLMProviderName.GROUNDED

    def default_model(self) -> str:
        return "grounded-v1"

    def available(self) -> bool:
        return True

    def complete(self, request: LLMRequest) -> LLMResponse:
        started = time.perf_counter()
        content = request.user_prompt
        latency_ms = (time.perf_counter() - started) * 1000.0
        tokens = max(1, len(content.split()))
        return LLMResponse(
            content=content,
            model=request.model or self.model,
            provider=self.name,
            prompt_tokens=max(1, len(request.system_prompt.split()) + len(request.user_prompt.split())),
            completion_tokens=tokens,
            total_tokens=max(1, len(request.system_prompt.split()) + len(request.user_prompt.split()) + tokens),
            latency_ms=latency_ms,
            cost_estimate_usd=0.0,
            raw={"mode": "grounded"},
        )
