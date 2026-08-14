from __future__ import annotations

import time

import httpx

from sales_copilot.llm.base import BaseLLMAdapter
from sales_copilot.models.types import LLMProviderName, LLMRequest, LLMResponse


class GeminiAdapter(BaseLLMAdapter):
    name = LLMProviderName.GEMINI

    def default_model(self) -> str:
        return "gemini-2.0-flash"

    def complete(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            raise RuntimeError("Gemini API key is not configured")
        started = time.perf_counter()
        model = request.model or self.model
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={self.api_key}"
        )
        payload = {
            "system_instruction": {"parts": [{"text": request.system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": request.user_prompt}]}],
            "generationConfig": {
                "temperature": request.temperature,
                "maxOutputTokens": request.max_tokens,
            },
        }
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
        latency_ms = (time.perf_counter() - started) * 1000.0
        candidates = data.get("candidates") or []
        parts = (((candidates[0] or {}).get("content") or {}).get("parts") or []) if candidates else []
        content = "".join(part.get("text", "") for part in parts)
        usage = data.get("usageMetadata") or {}
        prompt_tokens = int(usage.get("promptTokenCount") or 0)
        completion_tokens = int(usage.get("candidatesTokenCount") or 0)
        total_tokens = int(usage.get("totalTokenCount") or (prompt_tokens + completion_tokens))
        return LLMResponse(
            content=content,
            model=model,
            provider=self.name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            cost_estimate_usd=(prompt_tokens / 1_000_000) * 0.10 + (completion_tokens / 1_000_000) * 0.40,
            raw=data,
        )
