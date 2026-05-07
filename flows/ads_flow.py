"""
flows/ads_flow.py
CrowdWisdomTrading Ads AI — CrewAI Flow Orchestrator

Flow sequence:
  1. research_ads      → Apify scrapes Meta Ads, saves ads_raw.json
  2. extract_pain      → LLM extracts pain/marketing concepts, saves pain_concepts.json
  3. write_script      → LLM + GDrive data writes 7-scene ad script, saves ad_script.json
  4. produce_video     → Generates images, voiceover, renders Remotion video

Each step uses @listen to chain on the previous step's output.
State is carried in AdsFlowState (Pydantic model).
"""

import json
from pathlib import Path
from typing import Optional

from crewai import Crew, Process
from crewai.flow.flow import Flow, listen, start
from loguru import logger
from pydantic import BaseModel, Field

from agents import (
    build_ad_researcher,
    build_extraction_task,
    build_pain_extractor,
    build_production_task,
    build_research_task,
    build_script_task,
    build_script_writer,
    build_video_producer,
)
from config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Flow State
# ---------------------------------------------------------------------------


class AdsFlowState(BaseModel):
    """Shared state passed between flow steps."""

    niche: str = settings.target_niche
    brand: str = settings.target_brand
    website: str = settings.target_website

    # Outputs from each step (populated as flow progresses)
    ads_raw_json: str = ""          # JSON string of raw scraped ads
    top_ads_json: str = ""          # JSON string of top 10 selected ads
    pain_concepts_json: str = ""    # JSON string of extracted pain concepts
    ad_script_json: str = ""        # JSON string of the full ad script
    video_path: str = ""            # Path to rendered MP4
    audio_path: str = ""            # Path to voiceover MP3

    # Status tracking
    step_statuses: dict[str, str] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Flow Definition
# ---------------------------------------------------------------------------


class AdsFlow(Flow[AdsFlowState]):
    """
    Four-step CrewAI Flow that takes a niche and produces a rendered ad video.
    """

    # ── Step 1: Research ──────────────────────────────────────────────────
    @start()
    def research_ads(self) -> str:
        """
        Launch the Ad Researcher crew.
        Uses Apify to scrape Meta Ads Library and returns top ads JSON.
        """
        logger.info("=" * 60)
        logger.info("STEP 1 — Researching Meta Ads for niche: {}", self.state.niche)
        logger.info("=" * 60)

        researcher = build_ad_researcher()
        task = build_research_task(researcher)

        crew = Crew(
            agents=[researcher],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        try:
            result = crew.kickoff()
            output = result.raw if hasattr(result, "raw") else str(result)
            self.state.ads_raw_json = output
            self.state.step_statuses["research"] = "success"
            logger.success("STEP 1 complete — {} chars of ad data", len(output))
        except Exception as e:
            logger.error("STEP 1 FAILED: {}", e)
            self.state.errors.append(f"research: {e}")
            self.state.step_statuses["research"] = "failed"
            # Load from file if available (retry-safe)
            fallback = settings.outputs_dir / "ads_raw.json"
            if fallback.exists():
                self.state.ads_raw_json = fallback.read_text("utf-8")
                logger.info("Loaded fallback ads_raw.json from disk")

        return self.state.ads_raw_json

    # ── Step 2: Extract Pain Points ────────────────────────────────────────
    @listen(research_ads)
    def extract_pain(self, ads_json: str) -> str:
        """
        Launch the Pain Extractor crew.
        Analyses the scraped ads and extracts marketing DNA.
        """
        logger.info("=" * 60)
        logger.info("STEP 2 — Extracting pain points and marketing concepts")
        logger.info("=" * 60)

        if not ads_json or ads_json == "[]":
            logger.warning("No ads data to analyse — using sample data")
            ads_json = self._get_sample_ads_json()

        extractor = build_pain_extractor()
        task = build_extraction_task(extractor)

        # Inject ads data into task description
        task.description = task.description.replace("{ads_data}", ads_json[:6000])

        crew = Crew(
            agents=[extractor],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        try:
            result = crew.kickoff()
            output = result.raw if hasattr(result, "raw") else str(result)
            self.state.pain_concepts_json = output
            self.state.step_statuses["extraction"] = "success"
            logger.success("STEP 2 complete — pain concepts extracted")
        except Exception as e:
            logger.error("STEP 2 FAILED: {}", e)
            self.state.errors.append(f"extraction: {e}")
            self.state.step_statuses["extraction"] = "failed"
            fallback = settings.outputs_dir / "pain_concepts.json"
            if fallback.exists():
                self.state.pain_concepts_json = fallback.read_text("utf-8")

        return self.state.pain_concepts_json

    # ── Step 3: Write Script ───────────────────────────────────────────────
    @listen(extract_pain)
    def write_script(self, pain_json: str) -> str:
        """
        Launch the Script Writer crew.
        Fetches GDrive brand data + uses pain concepts to write the ad script.
        """
        logger.info("=" * 60)
        logger.info("STEP 3 — Writing 60-second ad script")
        logger.info("=" * 60)

        writer = build_script_writer()
        task = build_script_task(writer)

        crew = Crew(
            agents=[writer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        try:
            result = crew.kickoff(
                inputs={"pain_concepts": pain_json}
            )
            output = result.raw if hasattr(result, "raw") else str(result)
            self.state.ad_script_json = output
            self.state.step_statuses["script"] = "success"
            logger.success("STEP 3 complete — ad script written")
        except Exception as e:
            logger.error("STEP 3 FAILED: {}", e)
            self.state.errors.append(f"script: {e}")
            self.state.step_statuses["script"] = "failed"
            fallback = settings.outputs_dir / "ad_script.json"
            if fallback.exists():
                self.state.ad_script_json = fallback.read_text("utf-8")

        return self.state.ad_script_json

    # ── Step 4: Produce Video ──────────────────────────────────────────────
    @listen(write_script)
    def produce_video(self, script_json: str) -> str:
        """
        Launch the Video Producer crew.
        Generates images, voiceover, and renders Remotion video.
        """
        logger.info("=" * 60)
        logger.info("STEP 4 — Producing 60-second ad video")
        logger.info("=" * 60)

        producer = build_video_producer()
        task = build_production_task(producer)

        crew = Crew(
            agents=[producer],
            tasks=[task],
            process=Process.sequential,
            verbose=True,
        )

        try:
            result = crew.kickoff(
                inputs={"ad_script": script_json}
            )
            output = result.raw if hasattr(result, "raw") else str(result)
            self.state.video_path = self._extract_video_path(output)
            self.state.step_statuses["production"] = "success"
            logger.success("STEP 4 complete — video produced at: {}", self.state.video_path)
        except Exception as e:
            logger.error("STEP 4 FAILED: {}", e)
            self.state.errors.append(f"production: {e}")
            self.state.step_statuses["production"] = "failed"

        return self._build_summary()

    # ── Helpers ────────────────────────────────────────────────────────────

    def _extract_video_path(self, output: str) -> str:
        """Try to extract video_path from JSON output."""
        try:
            # Find JSON block in output
            start = output.find("{")
            end = output.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(output[start:end])
                return data.get("video_path", "")
        except Exception:
            pass
        # Fallback: look for .mp4 path
        for word in output.split():
            if word.endswith(".mp4"):
                return word
        return str(settings.videos_dir / "final_ad.mp4")

    def _build_summary(self) -> str:
        """Build a final summary of the flow run."""
        summary = {
            "brand": self.state.brand,
            "niche": self.state.niche,
            "step_statuses": self.state.step_statuses,
            "errors": self.state.errors,
            "outputs": {
                "ads_raw": str(settings.outputs_dir / "ads_raw.json"),
                "pain_concepts": str(settings.outputs_dir / "pain_concepts.json"),
                "ad_script": str(settings.outputs_dir / "ad_script.json"),
                "video": self.state.video_path or str(settings.videos_dir / "final_ad.mp4"),
                "voiceover": str(settings.outputs_dir / "audio" / "voiceover.mp3"),
            },
        }
        # Save summary
        summary_path = settings.outputs_dir / "run_summary.json"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.success("Run summary saved → {}", summary_path)
        return json.dumps(summary, indent=2)

    @staticmethod
    def _get_sample_ads_json() -> str:
        """Return sample ad data for testing when Apify returns nothing."""
        sample = [
            {
                "ad_id": "sample_001",
                "page_name": "TradeWise Academy",
                "ad_text": "Struggling to profit from the stock market? Most retail traders lose money because they're trading emotions, not data. Our AI-powered signals changed everything for 12,000+ members.",
                "ad_title": "Stop Losing Money on Trades",
                "call_to_action": "Get Free Access",
                "start_date": "2024-04-01",
                "estimated_reach": 500000,
                "platforms": ["facebook", "instagram"],
                "media_type": "video",
            },
            {
                "ad_id": "sample_002",
                "page_name": "WealthSignal Pro",
                "ad_text": "I was down $47,000 before I found this system. Now I'm consistently profitable. Here's the exact approach that changed my trading forever...",
                "ad_title": "From $47k Loss to Consistent Profits",
                "call_to_action": "Watch Free Training",
                "start_date": "2024-04-10",
                "estimated_reach": 380000,
                "platforms": ["facebook"],
                "media_type": "video",
            },
        ]
        return json.dumps(sample)
