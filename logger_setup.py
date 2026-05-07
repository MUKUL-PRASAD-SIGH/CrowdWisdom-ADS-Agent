"""
logger_setup.py
Configures loguru for the entire project.
Call `setup_logger()` once at startup from main.py.
"""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: Path = Path("logs"), level: str = "DEBUG") -> None:
    """
    Set up loguru with:
    - Colourised console output (INFO+)
    - Rotating file log in logs/ (DEBUG+)
    """
    log_dir.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Console: INFO and above, colourised
    logger.add(
        sys.stderr,
        level="INFO",
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
            "<level>{message}</level>"
        ),
    )

    # File: DEBUG and above, rotation + retention
    logger.add(
        log_dir / "ads_agent_{time:YYYY-MM-DD}.log",
        level=level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
            "{name}:{function}:{line} | {message}"
        ),
        enqueue=True,  # async-safe
    )

    logger.info("Logger initialised — level={} log_dir={}", level, log_dir)
