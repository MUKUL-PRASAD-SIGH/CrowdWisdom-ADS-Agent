# CrowdWisdom Ads Agent — Rate Limit Fix & Gemini Integration

## Problem Diagnosed

The pipeline was failing on **every single step** with `429 Rate Limit` errors. Root cause analysis revealed **three layers of rate limiting**:

| Limit | Value | Impact |
|-------|-------|--------|
| OpenRouter per-model RPM | 8 req/min | Moderate — causes intermittent failures |
| OpenRouter global free RPM | 16-20 req/min | High — affects all free models |
| **OpenRouter daily free cap** | **50 req/day** | **Fatal — hard daily limit, no retry possible** |

CrewAI agents make 5-15 LLM calls per task (think → tool → observe → think loop), so 4 agents × ~10 calls = **~40 LLM calls minimum** — nearly the entire daily budget in one run.

## Changes Made

### 1. `llm_with_retry.py` (NEW)
- **`RateLimitedLLM`** — Subclass of CrewAI's `LLM` that wraps `call()` with `tenacity` exponential backoff retry (15s → 30s → 60s → 120s, up to 8 attempts)
- **`build_llm()`** — Factory function that auto-detects the best available LLM provider:
  - Prefers **Google Gemini** if `GEMINI_API_KEY` is set (1500 req/day)
  - Falls back to **OpenRouter** if only `OPENROUTER_API_KEY` is set (50 req/day)

### 2. All 4 Agent Files Updated
- `agents/ad_researcher.py` — Uses `build_llm()` instead of hardcoded LLM
- `agents/pain_extractor.py` — Uses `build_llm()` instead of hardcoded LLM
- `agents/script_writer.py` — Uses `build_llm()` instead of hardcoded LLM
- `agents/video_producer.py` — Uses `build_llm()` instead of hardcoded LLM

### 3. `config.py`
- Added `gemini_api_key` and `gemini_model` settings
- Made `openrouter_api_key` optional (not required if Gemini is configured)

### 4. `flows/ads_flow.py`
- Added 30-second cooldown between steps to avoid cascading rate-limit hits

### 5. `.env`
- Added `GEMINI_API_KEY` and `GEMINI_MODEL` fields
- Clear documentation of each provider's free tier limits

### 6. `main.py`
- Config validation now shows active LLM provider and its rate limits
- `GEMINI_API_KEY` shown in the configuration check table

## How to Fix the Rate Limit Issue

### Option A: Use Google Gemini (FREE — recommended)

1. Go to **https://aistudio.google.com/apikey**
2. Click "Create API Key"
3. Copy the key
4. Paste into `.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```
5. Run: `python -X utf8 main.py`

### Option B: Add $1 to OpenRouter

1. Go to **https://openrouter.ai/settings/credits**
2. Add $1 credit (minimum)
3. This unlocks **1000 free model requests/day** (up from 50)
4. Run: `python -X utf8 main.py`

## Architecture

```
.env (GEMINI_API_KEY or OPENROUTER_API_KEY)
  └── config.py (Settings)
       └── llm_with_retry.py
            ├── build_llm()    ← Factory: auto-selects provider
            └── RateLimitedLLM ← Retry wrapper with backoff
                 └── All 4 agents use build_llm()
```
