"""
llm_with_retry.py
Custom LLM wrapper that adds exponential-backoff retry logic
on top of CrewAI's built-in LLM class.

Also provides a factory function `build_llm()` that automatically
selects the best available provider:
  1. Google Gemini (if GEMINI_API_KEY is set) — 1500 free req/day
  2. OpenRouter (fallback) — 50 free req/day

Problem:
    OpenRouter free-tier models enforce strict rate limits (50 req/day).
    CrewAI's `max_rpm` only throttles outgoing requests — if the upstream
    provider returns 429 *anyway*, CrewAI treats it as a fatal error and
    the agent crashes.

Solution:
    Subclass CrewAI's LLM and wrap the `call()` method with `tenacity`
    retry logic. Any 429 / RateLimitError is caught and retried with
    exponential backoff (wait 15-120s between retries, up to 8 attempts).
"""

import logging

from crewai import LLM
from tenacity import (
    retry,
    retry_if_exception_message,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger("llm_retry")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [RETRY] %(message)s"))
    logger.addHandler(handler)


class RateLimitedLLM(LLM):
    """
    Drop-in replacement for CrewAI's LLM that automatically retries
    on 429 / rate-limit errors with exponential backoff.

    Usage (identical to regular LLM):
        llm = RateLimitedLLM(
            model="gemini/gemini-2.5-flash",
            api_key="...",
        )
    """

    def call(self, *args, **kwargs):
        """Override call() to wrap with retry logic."""
        return self._call_with_retry(*args, **kwargs)

    @retry(
        retry=retry_if_exception_message(match=r"(?i).*(429|rate.limit).*"),
        stop=stop_after_attempt(8),
        wait=wait_exponential(multiplier=1, min=15, max=120),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _call_with_retry(self, *args, **kwargs):
        """
        Actual LLM call with tenacity retry.
        On 429 → waits 15s, 30s, 60s, 120s, ... up to 8 attempts.
        """
        return super().call(*args, **kwargs)


def build_llm() -> RateLimitedLLM:
    """
    Factory that returns a RateLimitedLLM configured for the best
    available provider. Checks in order:
      1. GEMINI_API_KEY → Google Gemini (free tier, 1500 req/day)
      2. OPENROUTER_API_KEY → OpenRouter (free tier, 50 req/day)

    This is the SINGLE place where LLM provider selection happens.
    All agents should call `build_llm()` instead of constructing LLM directly.
    """
    from config import get_settings
    settings = get_settings()

    # ── Prefer Gemini if API key is available ──────────────
    if settings.gemini_api_key:
        logger.info(
            "Using Google Gemini: %s (free tier: 1500 req/day)",
            settings.gemini_model,
        )
        return RateLimitedLLM(
            model=settings.gemini_model,
            api_key=settings.gemini_api_key,
        )

    # ── Fallback to OpenRouter ────────────────────────────
    if settings.openrouter_api_key:
        logger.info(
            "Using OpenRouter: %s (free tier: 50 req/day)",
            settings.openrouter_model,
        )
        return RateLimitedLLM(
            model=f"openrouter/{settings.openrouter_model}",
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )

    raise ValueError(
        "No LLM provider configured! Set either GEMINI_API_KEY or "
        "OPENROUTER_API_KEY in your .env file."
    )
