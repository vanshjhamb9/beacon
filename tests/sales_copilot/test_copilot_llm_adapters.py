from unittest.mock import MagicMock, patch

import pytest

from sales_copilot.llm.anthropic_adapter import AnthropicAdapter
from sales_copilot.llm.factory import LLMProviderConfig, LLMProviderFactory
from sales_copilot.llm.gemini_adapter import GeminiAdapter
from sales_copilot.llm.openai_adapter import OpenAIAdapter
from sales_copilot.llm.openrouter_adapter import OpenRouterAdapter
from sales_copilot.models.types import LLMProviderName, LLMRequest


def _request() -> LLMRequest:
    return LLMRequest(
        system_prompt="system",
        user_prompt="user",
        model="test-model",
        temperature=0.1,
        max_tokens=128,
    )


def test_adapters_require_api_keys() -> None:
    with pytest.raises(RuntimeError):
        OpenAIAdapter().complete(_request())
    with pytest.raises(RuntimeError):
        AnthropicAdapter().complete(_request())
    with pytest.raises(RuntimeError):
        GeminiAdapter().complete(_request())
    with pytest.raises(RuntimeError):
        OpenRouterAdapter().complete(_request())


def test_openai_adapter_parses_response() -> None:
    payload = {
        "model": "gpt-4o-mini",
        "choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    }
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = payload
    with patch("sales_copilot.llm.openai_adapter.httpx.Client") as client_cls:
        client = client_cls.return_value.__enter__.return_value
        client.post.return_value = mock_response
        result = OpenAIAdapter(api_key="sk-test").complete(_request())
    assert result.content == "ok"
    assert result.provider == LLMProviderName.OPENAI
    assert result.total_tokens == 15


def test_factory_selects_each_provider_when_keyed() -> None:
    factory = LLMProviderFactory(
        LLMProviderConfig(
            provider=LLMProviderName.GROUNDED,
            openai_api_key="a",
            anthropic_api_key="b",
            gemini_api_key="c",
            openrouter_api_key="d",
        )
    )
    assert factory.create(LLMProviderName.OPENAI).name == LLMProviderName.OPENAI
    assert factory.create(LLMProviderName.ANTHROPIC).name == LLMProviderName.ANTHROPIC
    assert factory.create(LLMProviderName.GEMINI).name == LLMProviderName.GEMINI
    assert factory.create(LLMProviderName.OPENROUTER).name == LLMProviderName.OPENROUTER
    assert factory.create(LLMProviderName.GROUNDED).name == LLMProviderName.GROUNDED
