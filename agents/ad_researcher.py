"""
agents/ad_researcher.py
Agent 1 — Ad Researcher
Searches Meta Ads Library via Apify for the best performing ads
in the CrowdWisdomTrading niche over the last 30 days.
Saves results to outputs/ads_raw.json.
"""

import json
from pathlib import Path

from crewai import Agent, Task
from loguru import logger

from config import get_settings
from llm_with_retry import build_llm
from tools.apify_tool import ApifyAdsTool

settings = get_settings()


def build_ad_researcher() -> Agent:
    """Construct and return the Ad Researcher agent."""
    logger.debug("Building AdResearcher agent")

    return Agent(
        role="Meta Ads Research Specialist",
        goal=(
            f"Find the TOP 10 highest-performing Meta (Facebook/Instagram) ads "
            f"in the '{settings.target_niche}' niche that have been active in the "
            f"last 30 days. Focus on ads with the highest estimated reach and engagement."
        ),
        backstory=(
            "You are a digital marketing analyst specialising in paid social media advertising. "
            "You have deep expertise in identifying winning ad patterns in the financial education "
            "and trading niche. You know exactly what makes an ad perform well — compelling hooks, "
            "clear pain points, strong CTAs, and social proof. "
            f"You are researching on behalf of {settings.target_brand} ({settings.target_website})."
        ),
        tools=[ApifyAdsTool()],
        llm=build_llm(),
        verbose=True,
        allow_delegation=False,
        max_retry_limit=3,
        max_rpm=5,
    )


def build_research_task(agent: Agent) -> Task:
    """Construct the research task for the Ad Researcher agent."""

    out_path = settings.outputs_dir / "ads_raw.json"

    return Task(
        description=(
            f"Search the Meta Ads Library for the best performing ads in the "
            f"'{settings.target_niche}' niche.\n\n"
            f"Requirements:\n"
            f"- Use the meta_ads_search tool with query: '{settings.target_niche}'\n"
            f"- Filter to ads active in the LAST 30 DAYS only\n"
            f"- Retrieve at least 50 ads and select the TOP 10 by estimated reach\n"
            f"- For each selected ad, capture: ad text, title, CTA, page name, start date, "
            f"  estimated reach, platforms, media type\n"
            f"- The tool automatically saves full results to outputs/ads_raw.json\n\n"
            f"Output a JSON array of the top 10 ads with all captured fields."
        ),
        expected_output=(
            "A JSON array of exactly 10 ad objects. Each object must include: "
            "ad_id, page_name, ad_text, ad_title, call_to_action, start_date, "
            "estimated_reach, platforms, media_type. "
            "Sorted by estimated_reach descending."
        ),
        agent=agent,
        output_file=str(out_path),
    )
