"""
tools/apify_tool.py
CrewAI custom tool that wraps Apify's Facebook/Meta Ads Library scraper.
Returns the top performing ads from the last 30 days for a given query.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Type

from apify_client import ApifyClient
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------


class ApifyAdsInput(BaseModel):
    """Input schema for ApifyAdsTool."""

    query: str = Field(
        description="Search query for Meta Ads Library (e.g. 'trading education')"
    )
    country: str = Field(default="US", description="Country code for the ad search")
    ad_category: str = Field(
        default="ALL",
        description="Ad category. Use 'ALL' for general, or 'FINANCIAL_PRODUCTS' etc.",
    )
    limit: int = Field(default=50, description="Maximum number of ads to retrieve")
    days_back: int = Field(default=30, description="Only return ads active in last N days")


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class ApifyAdsTool(BaseTool):
    """
    Searches the Meta (Facebook) Ads Library for active ads matching a query
    using Apify's `apify/facebook-ads-library-scraper` actor.

    Returns a JSON string of ad objects sorted by estimated reach (desc).
    """

    name: str = "meta_ads_search"
    description: str = (
        "Search Meta (Facebook/Instagram) Ads Library for successful ads "
        "matching a brand or niche. Returns structured ad data including "
        "creative text, impressions, and start date."
    )
    args_schema: Type[BaseModel] = ApifyAdsInput

    # ── Apify actor ID ─────────────────────────────────────────────────────
    ACTOR_ID: str = "apify/facebook-ads-library-scraper"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=30),
        reraise=True,
    )
    def _run(
        self,
        query: str,
        country: str = "US",
        ad_category: str = "ALL",
        limit: int = 50,
        days_back: int = 30,
    ) -> str:
        """Execute Apify actor and return filtered ads as JSON string."""
        logger.info(
            "ApifyAdsTool: querying Meta Ads Library | query='{}' country={} limit={}",
            query,
            country,
            limit,
        )

        client = ApifyClient(settings.apify_api_token)

        run_input = {
            "searchQuery": query,
            "adType": "ALL",
            "country": country,
            "adCategory": ad_category,
            "maxResults": limit,
            "addEstimatedReach": True,
        }

        try:
            run = client.actor(self.ACTOR_ID).call(run_input=run_input)
            logger.debug("Apify run completed | run_id={}", run.get("id"))
        except Exception as e:
            logger.error("Apify actor call failed: {}", e)
            raise

        # ── Collect dataset items ──────────────────────────────────────────
        dataset_id = run.get("defaultDatasetId")
        items: list[dict[str, Any]] = []
        for item in client.dataset(dataset_id).iterate_items():
            items.append(item)

        logger.info("Fetched {} raw ads from Apify", len(items))

        # ── Filter: last N days ────────────────────────────────────────────
        cutoff = datetime.utcnow() - timedelta(days=days_back)
        filtered: list[dict[str, Any]] = []

        for ad in items:
            start_date_str = ad.get("adStartDate") or ad.get("startDate") or ""
            try:
                if start_date_str:
                    ad_date = datetime.fromisoformat(start_date_str.replace("Z", ""))
                    if ad_date < cutoff:
                        continue  # too old
            except ValueError:
                pass  # if we can't parse date, include it anyway

            # ── Normalise fields ───────────────────────────────────────────
            normalised = {
                "ad_id": ad.get("adArchiveID") or ad.get("id", ""),
                "page_name": ad.get("pageName") or ad.get("advertiserName", ""),
                "ad_text": (
                    ad.get("adBody")
                    or ad.get("body")
                    or ad.get("snapshot", {}).get("body", {}).get("text", "")
                    or ""
                ),
                "ad_title": (
                    ad.get("title")
                    or ad.get("snapshot", {}).get("title", "")
                    or ""
                ),
                "call_to_action": (
                    ad.get("callToAction")
                    or ad.get("snapshot", {}).get("cta_text", "")
                    or ""
                ),
                "start_date": start_date_str,
                "estimated_reach": (
                    ad.get("estimatedAudienceSize", {}).get("upper_bound", 0)
                    if isinstance(ad.get("estimatedAudienceSize"), dict)
                    else ad.get("estimatedAudienceSize", 0)
                ),
                "impressions": ad.get("impressionsWithIndex", {}).get("impressionsText", "N/A"),
                "platforms": ad.get("publisherPlatform", []),
                "media_type": ad.get("adCreativeMediaType") or ad.get("mediaType", ""),
                "ad_url": ad.get("adSnapshotURL") or ad.get("snapshotURL", ""),
                "currency": ad.get("currency", "USD"),
                "spend": ad.get("spend", {}),
            }
            filtered.append(normalised)

        # ── Sort by estimated reach desc ───────────────────────────────────
        filtered.sort(key=lambda x: x.get("estimated_reach", 0), reverse=True)

        logger.info("Returning {} ads after filtering (last {} days)", len(filtered), days_back)

        # ── Save to outputs/ ───────────────────────────────────────────────
        out_path = settings.outputs_dir / "ads_raw.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(filtered, f, indent=2, ensure_ascii=False)

        logger.success("Saved raw ads → {}", out_path)

        return json.dumps(filtered, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tool = ApifyAdsTool()
    result = tool.run(
        {
            "query": "trading education stock market",
            "country": "US",
            "limit": 10,
            "days_back": 30,
        }
    )
    print(result[:500])
