# CrowdWisdom Ads Agent — Pipeline Status & Changes Log

## Latest Run: 2026-05-10 (ALL 4 STEPS ✅)

```
┌────────────┬───────────┐
│ Step       │ Status    │
├────────────┼───────────┤
│ research   │ ✓ success │
│ extraction │ ✓ success │
│ script     │ ✓ success │
│ production │ ✓ success │
└────────────┴───────────┘
Total time: 392.2s (~6.5 minutes)
```

### Output Files
| File | Size |
|------|------|
| ads_raw.json | 259 bytes |
| pain_concepts.json | 2,894 bytes |
| ad_script.json | 362 bytes |
| **voiceover.mp3** | **623 KB** |
| scene_1..7.jpg | Images generated |

---

## All Changes Made (Cumulative)

### 1. `llm_with_retry.py` — LLM Factory + Retry Wrapper
- `RateLimitedLLM`: exponential backoff on 429 errors (tenacity)
- `build_llm()`: auto-selects Gemini (preferred) or OpenRouter (fallback)

### 2. Agent Files — All Use `build_llm()` Factory
- `agents/ad_researcher.py`
- `agents/pain_extractor.py`
- `agents/script_writer.py`
- `agents/video_producer.py`
- `max_rpm` increased from 2 → 5 (Gemini supports 15 RPM)

### 3. `config.py` — Added Gemini Settings
- `gemini_api_key` / `gemini_model` fields
- `openrouter_api_key` made optional

### 4. `.env` — Gemini API Key Section
- `GEMINI_API_KEY` and `GEMINI_MODEL` added at top
- Clear documentation of provider limits

### 5. `main.py` — Enhanced Config Validation
- Shows active LLM provider and limits in startup table
- GEMINI_API_KEY shown in config check

### 6. `flows/ads_flow.py` — Cooldown Between Steps
- 30-second sleep between pipeline steps

### 7. `tools/apify_tool.py` — Fixed Meta Ads Scraper
- Actor ID: `leadsbrary/meta-ads-library-scraper`
- Input format: `startUrls` (Meta Ad Library search URLs)
- Field mapping updated for actor's output schema

### 8. `tools/gdrive_tool.py` — Fixed gdown API
- Removed unsupported `fuzzy=True` parameter

### 9. `requirements.txt` — Added `google-generativeai`

---

## Provider Comparison

| Provider | Free Tier | Rate Limit | Status |
|----------|-----------|------------|--------|
| **Google Gemini** | 1500 req/day | 15 RPM | ✅ Active |
| OpenRouter | 50 req/day | ~8 RPM | ❌ Exhausted |

## Remaining Items
1. **Remotion**: Run `cd remotion && npm install` to enable video rendering
2. **Apify**: Fixed input schema — will scrape real Meta ads on next run
3. **Pollinations**: Image API has rate limits — some scenes get placeholders
