"""Tests for LLM client — all with mocked OpenAI."""
import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from src.llm_client import (
    strip_pii,
    count_tokens,
    calculate_cost,
    parse_json_response,
)


class TestPIIStripping:
    def test_strips_email(self):
        text = "Contact john@example.com for details."
        result = strip_pii(text)
        assert "john@example.com" not in result
        assert "[EMAIL_REDACTED]" in result

    def test_strips_multiple_emails(self):
        text = "Email alice@test.com or bob@company.org."
        result = strip_pii(text)
        assert "alice@test.com" not in result
        assert "bob@company.org" not in result
        assert result.count("[EMAIL_REDACTED]") == 2

    def test_strips_phone_number(self):
        text = "Call +1-555-123-4567 for info."
        result = strip_pii(text)
        assert "555-123-4567" not in result
        assert "[PHONE_REDACTED]" in result

    def test_strips_international_phone(self):
        text = "Phone: +44 20 7946 0958"
        result = strip_pii(text)
        assert "7946" not in result

    def test_preserves_non_pii_text(self):
        text = "The regulation applies to all AI systems in the EU."
        assert strip_pii(text) == text

    def test_strips_mixed_pii(self):
        text = "Contact jane@acme.com or call 555-123-4567 for compliance help."
        result = strip_pii(text)
        assert "jane@acme.com" not in result
        assert "555-123-4567" not in result


class TestTokenCounting:
    def test_counts_tokens(self):
        tokens = count_tokens("Hello world")
        assert isinstance(tokens, int)
        assert tokens > 0

    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_long_text_more_tokens(self):
        short = count_tokens("Hello")
        long = count_tokens("Hello world, this is a longer text for token counting.")
        assert long > short


class TestCostCalculation:
    def test_gpt4o_cost(self):
        cost = calculate_cost(1000, 500, "gpt-4o")
        # 1000 input tokens * 0.005/1k + 500 output * 0.015/1k = 0.005 + 0.0075 = 0.0125
        assert abs(cost - 0.0125) < 0.001

    def test_gpt4o_mini_cost(self):
        cost = calculate_cost(1000, 500, "gpt-4o-mini")
        assert cost < calculate_cost(1000, 500, "gpt-4o")

    def test_zero_tokens(self):
        assert calculate_cost(0, 0, "gpt-4o") == 0.0

    def test_unknown_model_defaults_to_gpt4o(self):
        cost = calculate_cost(1000, 500, "unknown-model")
        assert cost == calculate_cost(1000, 500, "gpt-4o")


class TestLLMCallRetry:
    @pytest.mark.asyncio
    async def test_call_llm_retries_on_failure(self):
        from src.llm_client import call_llm

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "result"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        mock_create = AsyncMock(
            side_effect=[Exception("timeout"), Exception("rate limited"), mock_response]
        )

        mock_client_instance = MagicMock()
        mock_client_instance.chat = MagicMock()
        mock_client_instance.chat.completions = MagicMock()
        mock_client_instance.chat.completions.create = mock_create

        with patch("openai.AsyncOpenAI", return_value=mock_client_instance):
            with patch("src.llm_client.asyncio.sleep", new_callable=AsyncMock):
                result = await call_llm("Test prompt")
                assert result["content"] == "result"
                assert mock_create.call_count == 3

    @pytest.mark.asyncio
    async def test_call_llm_raises_after_max_retries(self):
        from src.llm_client import call_llm

        mock_create = AsyncMock(side_effect=Exception("persistent failure"))
        mock_client_instance = MagicMock()
        mock_client_instance.chat = MagicMock()
        mock_client_instance.chat.completions = MagicMock()
        mock_client_instance.chat.completions.create = mock_create

        with patch("openai.AsyncOpenAI", return_value=mock_client_instance):
            with patch("src.llm_client.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="failed after 3 retries"):
                    await call_llm("Test prompt")

    @pytest.mark.asyncio
    async def test_call_llm_rejects_over_token_limit(self):
        from src.llm_client import call_llm
        with pytest.raises(ValueError, match="exceeds token limit"):
            await call_llm("x " * 1000, token_limit=10)


class TestJSONParsing:
    def test_parses_plain_json(self):
        result = parse_json_response('{"key": "value"}')
        assert result["key"] == "value"

    def test_parses_json_in_code_block(self):
        result = parse_json_response('```json\n{"key": "value"}\n```')
        assert result["key"] == "value"

    def test_parses_json_array(self):
        result = parse_json_response('[{"a": 1}]')
        assert result[0]["a"] == 1

    def test_raises_on_invalid_json(self):
        with pytest.raises(Exception):
            parse_json_response("not json at all")
