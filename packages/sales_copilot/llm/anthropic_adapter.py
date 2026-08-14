from __future__ import annotations

import time

import httpx

from sales_copilot.llm.base import BaseLLMAdapter
from sales_copilot.models.types import LLMProviderName, LLMRequest, LLMResponse


class AnthropicAdapter(BaseLLMAdapter):
    name = LLMProviderName.ANTHROPIC

    def default_model(self) -> str:
        return "claude-3-5-haiku-latest"

    def complete(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise RuntimeError("Anthropic API key is not configured")
        started = time.perf_counter()
        payload = {
            "model": request.model or self.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "system": request.system_prompt,
            "messages": [{"role": "user", "content": request.user_prompt}],
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        latency_ms = (time.perf_counter() - started) * 1000.0
        blocks = data.get("content") or []
        content = "".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("input_tokens") or 0)
        completion_tokens = int(usage.get("output_tokens") or 0)
        return LLMResponse(
            content=content,
            model=data.get("model") or request.model or self.model,
            provider=self.name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=latency_ms,
            cost_estimate_usd=(prompt_tokens / 1_000_000) * 0.80 + (completion_tokens / 1_000_000) * 4.00,
            raw=data,
        )
