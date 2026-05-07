"""
tools/elevenlabs_tool.py
CrewAI tool that generates a voiceover MP3 using ElevenLabs TTS API.
Uses the free tier (10,000 chars/month on free plan).
"""

import time
from pathlib import Path
from typing import Optional, Type, ClassVar

import httpx
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------


class ElevenLabsInput(BaseModel):
    text: str = Field(description="The voiceover script text to convert to speech")
    voice_id: Optional[str] = Field(
        default=None,
        description="ElevenLabs voice ID. Defaults to env ELEVENLABS_VOICE_ID.",
    )
    output_filename: str = Field(
        default="voiceover.mp3", description="Output MP3 filename"
    )
    model_id: str = Field(
        default="eleven_multilingual_v2",
        description="ElevenLabs model ID",
    )
    stability: float = Field(default=0.5, description="Voice stability (0-1)")
    similarity_boost: float = Field(default=0.75, description="Voice clarity (0-1)")


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class ElevenLabsTool(BaseTool):
    """
    Converts a text script to an MP3 voiceover using ElevenLabs API.
    Returns the local path of the generated audio file.
    """

    name: str = "generate_voiceover"
    description: str = (
        "Convert a script text to a natural-sounding voiceover MP3 "
        "using ElevenLabs Text-to-Speech. Returns the audio file path."
    )
    args_schema: Type[BaseModel] = ElevenLabsInput

    BASE_URL: ClassVar[str] = "https://api.elevenlabs.io/v1"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=5, max=30),
        reraise=True,
    )
    def _run(
        self,
        text: str,
        voice_id: Optional[str] = None,
        output_filename: str = "voiceover.mp3",
        model_id: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75,
    ) -> str:
        """Call ElevenLabs API and save the audio file."""
        vid = voice_id or settings.elevenlabs_voice_id
        char_count = len(text)
        logger.info(
            "ElevenLabsTool: generating voiceover | voice_id={} chars={}",
            vid,
            char_count,
        )

        url = f"{self.BASE_URL}/text-to-speech/{vid}"
        headers = {
            "xi-api-key": settings.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        }

        with httpx.Client(timeout=90.0) as client:
            resp = client.post(url, json=payload, headers=headers)

        if resp.status_code != 200:
            logger.error(
                "ElevenLabs API error: {} — {}", resp.status_code, resp.text[:300]
            )
            raise RuntimeError(f"ElevenLabs API returned {resp.status_code}: {resp.text[:200]}")

        # ── Save audio ─────────────────────────────────────────────────────
        out_dir = settings.outputs_dir / "audio"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / output_filename

        with open(out_path, "wb") as f:
            f.write(resp.content)

        logger.success(
            "Voiceover saved → {} ({} bytes)", out_path, len(resp.content)
        )
        return str(out_path)

    # ── Helper: list available voices ─────────────────────────────────────
    def list_voices(self) -> list[dict]:
        """Utility method to list all available voices (for debugging)."""
        headers = {"xi-api-key": settings.elevenlabs_api_key}
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(f"{self.BASE_URL}/voices", headers=headers)
        resp.raise_for_status()
        voices = resp.json().get("voices", [])
        logger.info("Available ElevenLabs voices: {}", [v["name"] for v in voices])
        return voices
