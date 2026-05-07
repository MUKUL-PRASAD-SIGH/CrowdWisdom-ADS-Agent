"""
tools/image_gen_tool.py
Free image generation using Pollinations.ai (no API key required).
Falls back to a placeholder gradient image if the API is unreachable.
"""

import hashlib
import time
from pathlib import Path
from typing import Optional, Type

import httpx
from crewai.tools import BaseTool
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------


class ImageGenInput(BaseModel):
    prompt: str = Field(description="Text prompt describing the image to generate")
    width: int = Field(default=1080, description="Image width in pixels")
    height: int = Field(default=1920, description="Image height in pixels (9:16 for vertical video)")
    filename: Optional[str] = Field(default=None, description="Output filename (auto-generated if blank)")
    seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class ImageGenTool(BaseTool):
    """
    Generates images using Pollinations.ai (100% free, no API key).
    Saves results to outputs/ and returns the file path.
    """

    name: str = "generate_image"
    description: str = (
        "Generate an AI image from a text prompt using a free service. "
        "Returns the local file path of the generated image. "
        "Ideal for creating ad background visuals or scene images."
    )
    args_schema: Type[BaseModel] = ImageGenInput

    POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=4, max=20),
        reraise=False,
    )
    def _run(
        self,
        prompt: str,
        width: int = 1080,
        height: int = 1920,
        filename: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> str:
        """Generate image and return saved file path."""
        logger.info("ImageGenTool: generating image for prompt='{}'", prompt[:60])

        # ── Build filename ────────────────────────────────────────────────
        if not filename:
            slug = hashlib.md5(prompt.encode()).hexdigest()[:8]
            filename = f"scene_{slug}_{int(time.time())}.jpg"

        out_dir = settings.outputs_dir / "images"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / filename

        # ── Encode URL ────────────────────────────────────────────────────
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        seed_val = seed or int(time.time()) % 10000
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&seed={seed_val}&nologo=true"
        )

        try:
            logger.debug("Fetching from Pollinations: {}", url[:120])
            with httpx.Client(timeout=60.0, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()

            with open(out_path, "wb") as f:
                f.write(resp.content)

            logger.success("Image saved → {}", out_path)
            return str(out_path)

        except Exception as e:
            logger.warning("Pollinations failed ({}), creating placeholder image", e)
            return self._create_placeholder(out_path, prompt, width, height)

    # ── Fallback: gradient placeholder ────────────────────────────────────
    @staticmethod
    def _create_placeholder(
        out_path: Path, prompt: str, width: int, height: int
    ) -> str:
        """Create a dark gradient placeholder image with prompt text."""
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Gradient background (dark blue → dark purple)
        for y in range(height):
            r = int(10 + (y / height) * 20)
            g = int(10 + (y / height) * 5)
            b = int(40 + (y / height) * 60)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Overlay text
        try:
            font = ImageFont.truetype("arial.ttf", 36)
        except Exception:
            font = ImageFont.load_default()

        text = f"[Image Placeholder]\n{prompt[:100]}"
        draw.multiline_text(
            (width // 2, height // 2),
            text,
            fill=(255, 255, 255),
            font=font,
            anchor="mm",
            align="center",
        )

        img.save(str(out_path), "JPEG", quality=85)
        logger.info("Placeholder image saved → {}", out_path)
        return str(out_path)
