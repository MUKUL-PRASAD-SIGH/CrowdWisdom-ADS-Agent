"""
tools/gdrive_tool.py
CrewAI custom tool to fetch brand data from Google Drive.
Supports both public links (via gdown) and service-account-authenticated access.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Optional, Type

import gdown
from crewai.tools import BaseTool
from loguru import logger
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

settings = get_settings()


# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------


class GDriveInput(BaseModel):
    """Input schema for GDriveTool."""

    file_id: Optional[str] = Field(
        default=None,
        description="Google Drive file ID. If blank, uses GDRIVE_FILE_ID from env.",
    )
    output_filename: str = Field(
        default="brand_data.txt",
        description="Local filename to save the downloaded content.",
    )


# ---------------------------------------------------------------------------
# Tool Implementation
# ---------------------------------------------------------------------------


class GDriveTool(BaseTool):
    """
    Downloads a file from Google Drive and returns its text content.
    Supports .txt, .md, .json, .pdf (text extraction best-effort).
    """

    name: str = "gdrive_brand_data"
    description: str = (
        "Fetches CrowdWisdomTrading brand data, product descriptions, "
        "and educational content from a Google Drive file. "
        "Returns the raw text content of the file."
    )
    args_schema: Type[BaseModel] = GDriveInput

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=15),
        reraise=True,
    )
    def _run(
        self,
        file_id: Optional[str] = None,
        output_filename: str = "brand_data.txt",
    ) -> str:
        """Download from GDrive and return text content."""
        fid = file_id or settings.gdrive_file_id
        if not fid:
            logger.warning("No Google Drive file ID provided. Using dummy brand data.")
            return "CrowdWisdomTrading is an elite stock market education platform. We provide daily signals, live trading sessions, and proprietary indicators to help retail traders beat the market. Our unique value proposition is our AI-driven market sentiment analysis tool that predicts breakouts before they happen."

        logger.info("GDriveTool: downloading file_id={}", fid)

        # ── Determine download method ──────────────────────────────────────
        service_account_path = settings.gdrive_service_account_json
        out_path = settings.outputs_dir / output_filename
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if service_account_path and Path(service_account_path).exists():
            content = self._download_with_service_account(fid, out_path, service_account_path)
        else:
            content = self._download_public(fid, out_path)

        logger.success(
            "GDriveTool: downloaded {} chars of brand data", len(content)
        )
        return content

    # ── Private: public gdown download ────────────────────────────────────
    def _download_public(self, file_id: str, out_path: Path) -> str:
        url = f"https://drive.google.com/uc?id={file_id}"
        logger.debug("Downloading via gdown (public): {}", url)
        gdown.download(url, str(out_path), quiet=False, fuzzy=True)
        return self._read_file(out_path)

    # ── Private: service-account download ─────────────────────────────────
    def _download_with_service_account(
        self, file_id: str, out_path: Path, sa_json_path: str
    ) -> str:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseDownload
        import io

        SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
        creds = service_account.Credentials.from_service_account_file(
            sa_json_path, scopes=SCOPES
        )
        service = build("drive", "v3", credentials=creds)

        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.debug("GDrive download progress: {}%", int(status.progress() * 100))

        fh.seek(0)
        raw = fh.read()
        with open(out_path, "wb") as f:
            f.write(raw)

        return self._read_file(out_path)

    # ── Private: read file content ─────────────────────────────────────────
    @staticmethod
    def _read_file(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            try:
                import pdfplumber

                with pdfplumber.open(str(path)) as pdf:
                    return "\n".join(p.extract_text() or "" for p in pdf.pages)
            except ImportError:
                logger.warning("pdfplumber not installed; returning raw bytes as string")
                return path.read_text(encoding="utf-8", errors="ignore")
        elif suffix == ".json":
            return json.dumps(json.loads(path.read_text("utf-8")), indent=2)
        else:
            return path.read_text(encoding="utf-8", errors="ignore")
