"""OpenAI client wrapper with retry, token counting, cost tracking, and PII stripping."""
import asyncio
import json
import logging
import re
import time

import tiktoken

from shared.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# PII patterns to strip before sending to LLM
_EMAIL_RE = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
_PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")

# Rate limiting semaphore (respect OpenAI RPM limits)
_RPM_SEMAPHORE = asyncio.Semaphore(50)

# Cost per 1K tokens (gpt-4o pricing)
_COST_PER_1K = {
    "gpt-4o": {"input": 0.005, "output": 0.015},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}

_TIMEOUT = 120.0
_MAX_RETRIES = 3
_RETRY_DELAYS = [1.0, 2.0, 4.0]


def strip_pii(text: str) -> str:
    """Remove email addresses and phone numbers from text before LLM submission."""
    text = _EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    text = _PHONE_RE.sub("[PHONE_REDACTED]", text)
    return text


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def calculate_cost(input_tokens: int, output_tokens: int, model: str = "gpt-4o") -> float:
    """Calculate cost in USD for the given token usage."""
    pricing = _COST_PER_1K.get(model, _COST_PER_1K["gpt-4o"])
    return (input_tokens / 1000 * pricing["input"]) + (output_tokens / 1000 * pricing["output"])


async def call_llm(
    prompt: str,
    model: str | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.1,
    token_limit: int = 128_000,
) -> dict:
    """Call OpenAI with retry, token counting, rate limiting, and PII stripping.

    Returns dict with keys: content, input_tokens, output_tokens, cost, model, duration_ms.
    Raises RuntimeError after exhausting retries.
    """
    model = model or settings.openai_model

    # Strip PII before sending
    safe_prompt = strip_pii(prompt)

    # Token limit check
    input_tokens = count_tokens(safe_prompt, model)
    if input_tokens > token_limit:
        raise ValueError(
            f"Prompt exceeds token limit: {input_tokens} > {token_limit}"
        )

    # Never log prompt content (may contain sensitive regulatory text)
    logger.info("LLM call: model=%s, input_tokens=%d", model, input_tokens)

    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        timeout=_TIMEOUT,
    )

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with _RPM_SEMAPHORE:
                start = time.perf_counter()
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": safe_prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                duration_ms = int((time.perf_counter() - start) * 1000)

            usage = response.usage
            output_tokens = usage.completion_tokens if usage else 0
            actual_input = usage.prompt_tokens if usage else input_tokens
            cost = calculate_cost(actual_input, output_tokens, model)

            return {
                "content": response.choices[0].message.content,
                "input_tokens": actual_input,
                "output_tokens": output_tokens,
                "cost": cost,
                "model": model,
                "duration_ms": duration_ms,
            }
        except Exception as exc:
            last_error = exc
            if attempt < _MAX_RETRIES:
                delay = _RETRY_DELAYS[attempt - 1]
                logger.warning(
                    "LLM call attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt, _MAX_RETRIES, type(exc).__name__, delay,
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    "LLM call failed after %d attempts: %s", _MAX_RETRIES, exc,
                )

    raise RuntimeError(f"LLM call failed after {_MAX_RETRIES} retries: {last_error}")


def parse_json_response(content: str) -> dict | list:
    """Parse JSON from LLM response, handling markdown code blocks."""
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        content = "\n".join(lines)
    return json.loads(content)
