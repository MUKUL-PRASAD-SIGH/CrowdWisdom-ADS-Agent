"""
agents/script_writer.py
Agent 3 — Ad Script Writer
Fetches brand/product data from Google Drive and combines it with
the extracted pain points to write a compelling 60-second ad script.
Saves result to outputs/ad_script.json.
"""

import json
from pathlib import Path
from typing import Optional

from crewai import Agent, Task
from loguru import logger
from pydantic import BaseModel, Field

from config import get_settings
from llm_with_retry import build_llm
from tools.gdrive_tool import GDriveTool

settings = get_settings()


# ---------------------------------------------------------------------------
# Pydantic schema for structured script output
# ---------------------------------------------------------------------------


class SceneInstruction(BaseModel):
    scene_number: int
    duration_seconds: float = Field(description="How long this scene should last")
    visual_description: str = Field(description="What should be shown on screen visually")
    voiceover_text: str = Field(description="Exact words spoken in this scene")
    on_screen_text: str = Field(description="Text overlay / subtitle shown on screen")
    background_music_mood: str = Field(
        description="Music mood suggestion: energetic, tense, inspiring, calm"
    )
    image_prompt: str = Field(
        description="Detailed prompt for AI image generation for this scene's background"
    )


class AdScript(BaseModel):
    title: str = Field(description="Internal title for this ad concept")
    hook: str = Field(description="The opening hook line (first 3 seconds, must stop the scroll)")
    target_pain_point: str = Field(description="The primary pain point this ad addresses")
    emotional_journey: str = Field(
        description="Pain → Agitate → Solution → CTA emotional arc description"
    )
    full_voiceover: str = Field(description="Complete voiceover text for the full 60-second ad")
    scenes: list[SceneInstruction] = Field(description="Scene-by-scene breakdown")
    call_to_action: str = Field(description="Final CTA text shown at the end")
    total_duration_seconds: float = Field(description="Total video duration (should be ~60)")
    target_audience: str = Field(description="Who this ad is for")
    brand_unique_value: str = Field(
        description="What makes CrowdWisdomTrading's offer unique in this ad"
    )


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------


def build_script_writer() -> Agent:
    """Construct and return the Script Writer agent."""
    logger.debug("Building ScriptWriter agent")

    return Agent(
        role="Direct-Response Ad Copywriter & Video Script Specialist",
        goal=(
            "Write a compelling, emotionally engaging 60-second video ad script for "
            f"{settings.target_brand} that leverages identified pain points and the brand's "
            "unique data/product advantages. The script must be structured scene-by-scene "
            "with voiceover, visuals, and on-screen text."
        ),
        backstory=(
            "You are an elite direct-response copywriter who has written scripts for "
            "multi-million dollar ad campaigns in the fintech and trading education space. "
            "You know the proven PAS (Pain-Agitate-Solution) and AIDA frameworks inside out. "
            "You specialise in 60-second vertical video scripts optimised for Meta and TikTok. "
            "Your scripts have a pattern-interrupting hook in the first 3 seconds, build "
            "emotional tension in the middle, and drive action with a clear CTA at the end. "
            "You also understand how to weave in specific product data and social proof to "
            "build credibility and trust."
        ),
        tools=[GDriveTool()],
        llm=build_llm(),
        verbose=True,
        allow_delegation=False,
        max_retry_limit=3,
        max_rpm=5,
    )


def build_script_task(agent: Agent) -> Task:
    """Construct the script writing task."""

    out_path = settings.outputs_dir / "ad_script.json"

    return Task(
        description=(
            "Create a complete 60-second video ad script for CrowdWisdomTrading.\n\n"
            "STEP 1: Use the gdrive_brand_data tool to fetch the brand/product data "
            "from Google Drive.\n\n"
            "STEP 2: Using the pain concepts from the previous analysis AND the brand data, "
            "write a complete ad script following this structure:\n\n"
            "SCENE BREAKDOWN (60 seconds total):\n"
            "  • Scene 1 (0-3s):  HOOK — Pattern interrupt, stop the scroll\n"
            "  • Scene 2 (3-10s): PAIN — Amplify the core pain point\n"
            "  • Scene 3 (10-20s): AGITATE — Make the problem feel urgent/real\n"
            "  • Scene 4 (20-35s): SOLUTION — Introduce CrowdWisdomTrading's approach\n"
            "  • Scene 5 (35-50s): PROOF — Social proof, results, credibility signals\n"
            "  • Scene 6 (50-57s): OFFER — Specific offer with urgency\n"
            "  • Scene 7 (57-60s): CTA — Clear single action\n\n"
            "For EACH scene, provide:\n"
            "  - Exact voiceover text (spoken words)\n"
            "  - Visual description (what's on screen)\n"
            "  - On-screen text overlay\n"
            "  - Image generation prompt for the background\n"
            "  - Music mood\n\n"
            "GUIDELINES:\n"
            "  - Hook must be under 3 seconds and emotionally provocative\n"
            "  - Use specific numbers/data from the brand data where possible\n"
            "  - Voiceover should read naturally when spoken aloud at moderate pace\n"
            "  - Total voiceover word count: 120-160 words (suits 60s at ~150 WPM)\n"
            "  - CTA: ONE clear action (e.g. 'Click the link below to get free access')\n\n"
            "Output valid JSON matching the AdScript schema."
        ),
        expected_output=(
            "A valid JSON object matching the AdScript schema with: title, hook, "
            "target_pain_point, emotional_journey, full_voiceover, scenes (7 SceneInstruction "
            "objects), call_to_action, total_duration_seconds (~60), target_audience, "
            "brand_unique_value. Must be parseable JSON."
        ),
        agent=agent,
        output_file=str(out_path),
        context_variables={
            "pain_concepts_path": str(settings.outputs_dir / "pain_concepts.json")
        },
    )
