"""
tools/remotion_tool.py
CrewAI tool that drives the Remotion CLI to render a video composition.
Writes the ad data bundle for Remotion to consume, then shells out to
`npx remotion render`.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Optional, Type

from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed

from config import get_settings

settings = get_settings()

REMOTION_DIR = Path(__file__).parent.parent / "remotion"


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------


class RemotionRenderInput(BaseModel):
    composition_id: str = Field(
        default="AdVideo",
        description="Remotion composition ID to render (must match Root.tsx)",
    )
    output_filename: str = Field(
        default="final_ad.mp4", description="Output video filename"
    )
    props_json: str = Field(
        description="JSON string of props to pass to the Remotion composition"
    )
    duration_seconds: int = Field(
        default=60, description="Duration of the ad video in seconds"
    )
    fps: int = Field(default=30, description="Frames per second")
    width: int = Field(default=1080, description="Video width in pixels")
    height: int = Field(default=1920, description="Video height in pixels")


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class RemotionRenderTool(BaseTool):
    """
    Renders a Remotion video composition to an MP4 file.

    Steps:
    1. Writes props to remotion/src/props.json so the React components can read them.
    2. Runs `npx remotion render` via subprocess.
    3. Returns the absolute path to the rendered video.
    """

    name: str = "render_video"
    description: str = (
        "Render a 60-second ad video using Remotion. "
        "Pass structured ad data as JSON props. "
        "Returns the file path of the rendered MP4."
    )
    args_schema: Type[BaseModel] = RemotionRenderInput

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(5), reraise=True)
    def _run(
        self,
        composition_id: str = "AdVideo",
        output_filename: str = "final_ad.mp4",
        props_json: str = "{}",
        duration_seconds: int = 60,
        fps: int = 30,
        width: int = 1080,
        height: int = 1920,
    ) -> str:
        """Write props and invoke Remotion CLI render."""
        logger.info(
            "RemotionRenderTool: rendering {} | {}s @ {}fps", composition_id, duration_seconds, fps
        )

        # ── Ensure remotion deps are installed ────────────────────────────
        self._ensure_deps()

        # ── Write props bundle for Remotion to consume ────────────────────
        props_path = REMOTION_DIR / "src" / "props.json"
        props_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            props_data = json.loads(props_json)
        except json.JSONDecodeError as e:
            logger.warning("Invalid props JSON, using empty: {}", e)
            props_data = {}

        # Inject render metadata
        props_data.update(
            {
                "durationSeconds": duration_seconds,
                "fps": fps,
                "width": width,
                "height": height,
            }
        )
        with open(props_path, "w", encoding="utf-8") as f:
            json.dump(props_data, f, indent=2)

        logger.debug("Props written → {}", props_path)

        # ── Build output path ─────────────────────────────────────────────
        out_dir = settings.videos_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / output_filename

        # ── Remotion render command ───────────────────────────────────────
        cmd = [
            "npx",
            "remotion",
            "render",
            composition_id,
            str(out_path),
            f"--props={props_path}",
            f"--frames=0-{duration_seconds * fps - 1}",
            "--overwrite",
            "--log=verbose",
        ]

        logger.info("Running: {}", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                cwd=str(REMOTION_DIR),
                capture_output=True,
                text=True,
                timeout=600,  # 10 min max
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Remotion render timed out after 10 minutes")
        except FileNotFoundError:
            raise RuntimeError(
                "Node.js / npx not found. Install Node.js 18+ and run `npm install` in the remotion/ directory."
            )

        if result.returncode != 0:
            logger.error("Remotion stderr: {}", result.stderr[-1000:])
            raise RuntimeError(
                f"Remotion render failed (exit {result.returncode}): {result.stderr[-500:]}"
            )

        logger.success("Video rendered → {}", out_path)
        return str(out_path)

    # ── Ensure node_modules exist ─────────────────────────────────────────
    @staticmethod
    def _ensure_deps() -> None:
        nm = REMOTION_DIR / "node_modules"
        if not nm.exists():
            logger.info("Installing Remotion npm dependencies...")
            result = subprocess.run(
                ["npm", "install"],
                cwd=str(REMOTION_DIR),
                capture_output=True,
                text=True,
                timeout=180,
            )
            if result.returncode != 0:
                logger.warning("npm install warning: {}", result.stderr[-500:])
            else:
                logger.success("npm install complete")
