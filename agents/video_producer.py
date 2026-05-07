"""
agents/video_producer.py
Agent 4 — Video Producer
Takes the ad script and orchestrates:
  1. Image generation per scene (Pollinations.ai — free)
  2. Full voiceover generation (ElevenLabs)
  3. Remotion video render with subtitles
Saves final video to outputs/videos/final_ad.mp4
"""

import json
from pathlib import Path
from typing import Optional

from crewai import Agent, Task, LLM
from loguru import logger
from pydantic import BaseModel, Field

from config import get_settings
from tools.elevenlabs_tool import ElevenLabsTool
from tools.image_gen_tool import ImageGenTool
from tools.remotion_tool import RemotionRenderTool

settings = get_settings()


# ---------------------------------------------------------------------------
# Pydantic schema for video production output
# ---------------------------------------------------------------------------


class VideoProductionResult(BaseModel):
    video_path: str = Field(description="Absolute path to the rendered MP4 file")
    audio_path: str = Field(description="Absolute path to the voiceover MP3 file")
    scene_images: list[str] = Field(description="List of paths to generated scene images")
    total_scenes: int = Field(description="Number of scenes rendered")
    duration_seconds: float = Field(description="Final video duration")
    render_notes: str = Field(description="Any notes or warnings from the render process")


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------


def build_video_producer() -> Agent:
    """Construct and return the Video Producer agent."""
    logger.debug("Building VideoProducer agent")

    return Agent(
        role="AI Video Production Director",
        goal=(
            "Transform the ad script into a polished 60-second video by generating "
            "scene visuals, producing the voiceover, and rendering the final video "
            "using Remotion. Ensure all assets are correctly linked and the final "
            "MP4 is ready to upload to Meta Ads."
        ),
        backstory=(
            "You are a digital video production director who specialises in AI-assisted "
            "ad creation for social media. You orchestrate multiple AI tools seamlessly — "
            "from image generation to text-to-speech to video composition. "
            "You know exactly what parameters each tool needs, always validate outputs, "
            "and handle errors gracefully. You ensure the final video is optimised for "
            "vertical (9:16) social media placement with clear subtitles and "
            "a punchy audio-visual rhythm."
        ),
        tools=[ImageGenTool(), ElevenLabsTool(), RemotionRenderTool()],
        llm=LLM(
            model=f"openrouter/{settings.openrouter_model}",
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        ),
        verbose=True,
        allow_delegation=False,
        max_retry_limit=2,
    )


def build_production_task(agent: Agent) -> Task:
    """Construct the video production task."""

    out_path = settings.videos_dir / "final_ad.mp4"

    return Task(
        description=(
            "Produce a complete 60-second video ad from the script in outputs/ad_script.json.\n\n"
            "Execute these steps IN ORDER:\n\n"
            "STEP 1 — Generate scene images\n"
            "  For each scene in the script, call the generate_image tool with:\n"
            "  - prompt: the scene's image_prompt field\n"
            "  - width: 1080, height: 1920 (vertical 9:16)\n"
            "  - filename: scene_1.jpg, scene_2.jpg, etc.\n"
            "  Collect all returned file paths.\n\n"
            "STEP 2 — Generate voiceover\n"
            "  Call the generate_voiceover tool with:\n"
            "  - text: the full_voiceover field from the script\n"
            "  - output_filename: voiceover.mp3\n"
            "  Save the returned audio path.\n\n"
            "STEP 3 — Render video with Remotion\n"
            "  Call the render_video tool with:\n"
            "  - composition_id: 'AdVideo'\n"
            "  - output_filename: 'final_ad.mp4'\n"
            "  - duration_seconds: 60\n"
            "  - fps: 30\n"
            "  - props_json: A JSON string containing:\n"
            "    {\n"
            "      'scenes': [array of scene objects with imagePath, voiceoverText, onScreenText, durationSeconds],\n"
            "      'audioPath': '<path from step 2>',\n"
            "      'brandName': 'CrowdWisdomTrading',\n"
            "      'callToAction': '<cta from script>',\n"
            "      'brandColor': '#00D4AA'\n"
            "    }\n\n"
            "STEP 4 — Report results\n"
            "  Return a JSON object with: video_path, audio_path, scene_images list, "
            "  total_scenes, duration_seconds, render_notes.\n\n"
            "If any step fails, document the error in render_notes and continue with "
            "what's available. NEVER abort the entire task for a single step failure."
        ),
        expected_output=(
            "A JSON object with video_path (path to final_ad.mp4), audio_path (path to "
            "voiceover.mp3), scene_images (list of image paths), total_scenes (int), "
            "duration_seconds (float ~60), render_notes (string). "
            "The video_path must point to an existing rendered MP4 file."
        ),
        agent=agent,
        output_file=str(settings.outputs_dir / "production_result.json"),
    )
