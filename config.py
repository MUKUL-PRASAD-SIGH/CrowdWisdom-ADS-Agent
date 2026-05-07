"""
config.py
Centralised settings loaded from environment variables via pydantic-settings.
All agents and tools import from here — never read os.environ directly.
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

# Load .env file from project root
load_dotenv(Path(__file__).parent / ".env")


class Settings(BaseSettings):
    # ── OpenRouter / LLM ──────────────────────────────────
    openrouter_api_key: str = Field(..., env="OPENROUTER_API_KEY")
    openrouter_model: str = Field(
        default="meta-llama/llama-3.3-8b-instruct:free", env="OPENROUTER_MODEL"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL"
    )

    # ── Apify ─────────────────────────────────────────────
    apify_api_token: str = Field(..., env="APIFY_API_TOKEN")

    # ── ElevenLabs ────────────────────────────────────────
    elevenlabs_api_key: str = Field(..., env="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(
        default="EXAVITQu4vr4xnSDxMaL", env="ELEVENLABS_VOICE_ID"
    )

    # ── Google Drive ──────────────────────────────────────
    gdrive_file_id: str = Field(..., env="GDRIVE_FILE_ID")
    gdrive_service_account_json: str = Field(default="", env="GDRIVE_SERVICE_ACCOUNT_JSON")

    # ── Target ────────────────────────────────────────────
    target_niche: str = Field(
        default="trading education stock market signals", env="TARGET_NICHE"
    )
    target_brand: str = Field(default="CrowdWisdomTrading", env="TARGET_BRAND")
    target_website: str = Field(
        default="https://www.crowdwisdomtrading.com", env="TARGET_WEBSITE"
    )
    ad_duration_seconds: int = Field(default=60, env="AD_DURATION_SECONDS")

    # ── Paths (derived) ───────────────────────────────────
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent

    @property
    def outputs_dir(self) -> Path:
        return self.project_root / "outputs"

    @property
    def videos_dir(self) -> Path:
        return self.outputs_dir / "videos"

    @property
    def logs_dir(self) -> Path:
        return self.project_root / "logs"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
