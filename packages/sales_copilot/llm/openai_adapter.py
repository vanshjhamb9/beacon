from __future__ import annotations

import time

import httpx

from sales_copilot.llm.base import BaseLLMAdapter
from sales_copilot.models.types import LLMProviderName, LLMRequest, LLMResponse


class OpenAIAdapter(BaseLLMAdapter):
    name = LLMProviderName.OPENAI

    def default_model(self) -> str:
        return "gpt-4o-mini"

    def complete(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise RuntimeError("OpenAI API key is not configured")
        started = time.perf_counter()
        payload = {
            "model": request.model or self.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        latency_ms = (time.perf_counter() - started) * 1000.0
        usage = data.get("usage") or {}
        content = data["choices"][0]["message"]["content"]
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        total_tokens = int(usage.get("total_tokens") or (prompt_tokens + completion_tokens))
        return LLMResponse(
            content=content,
            model=data.get("model") or request.model or self.model,
            provider=self.name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_estimate_usd=_openai_cost(request.model or self.model, prompt_tokens, completion_tokens),
            raw=data,
        )


def _openai_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    # Approximate USD estimates for logging; not billing-accurate.
    rates = {
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
    }
    input_rate, output_rate = rates.get(model, (0.15, 0.60))
    return (prompt_tokens / 1_000_000) * input_rate + (completion_tokens / 1_000_000) * output_rate
