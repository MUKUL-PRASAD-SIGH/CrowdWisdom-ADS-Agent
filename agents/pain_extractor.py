"""
agents/pain_extractor.py
Agent 2 — Pain Point & Marketing Concept Extractor
Analyses the top performing ads and extracts:
  - Core pain points being addressed
  - Marketing angles / hooks
  - Emotional triggers
  - Offer structures
  - Power words used
Saves structured results to outputs/pain_concepts.json
"""

import json
from pathlib import Path
from typing import Optional

from crewai import Agent, Task, LLM
from loguru import logger
from pydantic import BaseModel, Field

from config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Pydantic schema for structured output
# ---------------------------------------------------------------------------


class PainConcept(BaseModel):
    pain_point: str = Field(description="The core fear, frustration or desire being addressed")
    marketing_angle: str = Field(description="The hook or angle used to attract attention")
    emotional_trigger: str = Field(
        description="Primary emotional lever (fear, greed, FOMO, aspiration, curiosity)"
    )
    power_words: list[str] = Field(description="High-impact words and phrases used in the ad")
    offer_structure: str = Field(
        description="How the offer is framed (free trial, guarantee, urgency, scarcity)"
    )
    target_audience: str = Field(description="Who the ad is clearly targeting")
    ad_format_insight: str = Field(
        description="What makes the format/structure of this ad effective"
    )
    source_ad_id: str = Field(description="The ad_id this was extracted from")


class ExtractionResult(BaseModel):
    concepts: list[PainConcept]
    top_pain_points: list[str] = Field(description="Top 5 pain points across all analysed ads")
    winning_hooks: list[str] = Field(description="Top 5 most effective hooks / opening lines")
    recommended_cta: str = Field(description="Best CTA pattern seen across the ads")
    niche_insights: str = Field(
        description="Overall insights about what is working in this niche right now"
    )


# ---------------------------------------------------------------------------
# Agent builder
# ---------------------------------------------------------------------------


def build_pain_extractor() -> Agent:
    """Construct and return the Pain Point Extractor agent."""
    logger.debug("Building PainExtractor agent")

    return Agent(
        role="Marketing Psychology & Copywriting Analyst",
        goal=(
            "Extract the core pain points, emotional triggers, and marketing frameworks "
            "from a set of top-performing Meta ads. Identify patterns and synthesise "
            "actionable insights for creating a high-converting ad script."
        ),
        backstory=(
            "You are a world-class direct-response copywriter and consumer psychology expert "
            "with 15 years of experience in financial services marketing. "
            "You have studied thousands of winning ads and can instantly identify "
            "the psychological levers that make them convert. "
            "You understand the unique fears and desires of retail traders: fear of missing out, "
            "fear of losing money, desire for financial freedom, frustration with complex systems, "
            "and aspiration to beat the market. "
            "You break down ads into their core components and extract reusable marketing DNA."
        ),
        llm=LLM(
            model=f"openrouter/{settings.openrouter_model}",
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        ),
        verbose=True,
        allow_delegation=False,
        max_retry_limit=3,
    )


def build_extraction_task(agent: Agent, ads_json: str = "") -> Task:
    """Construct the extraction task for the Pain Point Extractor agent."""

    out_path = settings.outputs_dir / "pain_concepts.json"

    return Task(
        description=(
            "Analyse the following top-performing Meta ads from the trading education niche "
            "and extract the marketing DNA from each one.\n\n"
            "INPUT ADS DATA:\n"
            "{ads_data}\n\n"
            "For EACH ad, extract:\n"
            "1. Core pain point being addressed\n"
            "2. Marketing angle / hook\n"
            "3. Primary emotional trigger (fear, FOMO, greed, aspiration, curiosity)\n"
            "4. Power words and high-impact phrases\n"
            "5. Offer structure (how is the deal framed?)\n"
            "6. Target audience profile\n"
            "7. Format/structural insight (what makes this ad's structure effective?)\n\n"
            "Then synthesise ACROSS all ads:\n"
            "- Top 5 pain points that appear most frequently\n"
            "- Top 5 winning hooks / opening lines\n"
            "- Best CTA pattern seen\n"
            "- Overall niche insights\n\n"
            f"Context: You are extracting insights for {settings.target_brand}, "
            f"a trading education platform at {settings.target_website}.\n\n"
            "Output valid JSON matching the ExtractionResult schema."
        ),
        expected_output=(
            "A valid JSON object with keys: "
            "'concepts' (array of PainConcept objects), "
            "'top_pain_points' (list of 5 strings), "
            "'winning_hooks' (list of 5 strings), "
            "'recommended_cta' (string), "
            "'niche_insights' (string). "
            "Must be parseable JSON."
        ),
        agent=agent,
        output_file=str(out_path),
    )
