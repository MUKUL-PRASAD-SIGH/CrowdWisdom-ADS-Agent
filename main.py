"""
main.py
CrowdWisdomTrading Ads AI Agent — Entry Point

Usage:
    python main.py                  # Run full pipeline
    python main.py --step research  # Run only step 1
    python main.py --step extract   # Run only step 2
    python main.py --step script    # Run only step 3
    python main.py --step video     # Run only step 4
    python main.py --dry-run        # Validate config without running
"""

import json
import sys
import time
from pathlib import Path
from typing import Optional

import typer
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# ── Local imports ──────────────────────────────────────────────────────────
from config import get_settings
from logger_setup import setup_logger
from flows.ads_flow import AdsFlow, AdsFlowState

app = typer.Typer(
    name="cwt-ads-agent",
    help="CrowdWisdomTrading Daily Ads AI Agent — generate high-converting ad videos.",
    add_completion=False,
)
console = Console()


# ---------------------------------------------------------------------------
# CLI Commands
# ---------------------------------------------------------------------------


@app.command()
def run(
    step: Optional[str] = typer.Option(
        None,
        "--step",
        "-s",
        help="Run a specific step only: research | extract | script | video",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Validate configuration without executing"
    ),
    niche: Optional[str] = typer.Option(
        None, "--niche", help="Override target niche (default from .env)"
    ),
    log_level: str = typer.Option("DEBUG", "--log-level", help="Log level"),
):
    """
    Run the CrowdWisdomTrading Ads AI pipeline.
    """
    settings = get_settings()
    setup_logger(log_dir=settings.logs_dir, level=log_level)

    # ── Welcome banner ─────────────────────────────────────────────────────
    console.print(
        Panel.fit(
            "[bold cyan]CrowdWisdomTrading Ads AI Agent[/bold cyan]\n"
            "[dim]Powered by CrewAI • OpenRouter • Apify • ElevenLabs • Remotion[/dim]",
            border_style="cyan",
        )
    )

    # ── Config validation ──────────────────────────────────────────────────
    _validate_config(settings)

    if dry_run:
        console.print("[green]✓ Dry run complete — configuration is valid.[/green]")
        return

    # ── Ensure output directories exist ───────────────────────────────────
    for d in [settings.outputs_dir, settings.videos_dir, settings.logs_dir,
              settings.outputs_dir / "audio", settings.outputs_dir / "images"]:
        d.mkdir(parents=True, exist_ok=True)

    # ── Override niche if provided ─────────────────────────────────────────
    effective_niche = niche or settings.target_niche

    # ── Run flow ───────────────────────────────────────────────────────────
    start_time = time.time()

    try:
        if step:
            _run_single_step(step, effective_niche, settings)
        else:
            _run_full_flow(effective_niche)

    except KeyboardInterrupt:
        console.print("\n[yellow]Pipeline interrupted by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger.exception("Pipeline failed with unexpected error")
        console.print(f"[red]✗ Pipeline failed: {e}[/red]")
        sys.exit(1)

    elapsed = time.time() - start_time
    console.print(
        Panel.fit(
            f"[bold green]✓ Pipeline complete![/bold green]\n"
            f"Total time: [cyan]{elapsed:.1f}s[/cyan]\n"
            f"Outputs in: [cyan]{settings.outputs_dir}[/cyan]",
            border_style="green",
        )
    )

    # ── Print output summary table ─────────────────────────────────────────
    _print_output_summary(settings)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run_full_flow(niche: str) -> None:
    """Execute the full 4-step CrewAI Flow."""
    logger.info("Starting full pipeline for niche: {}", niche)
    console.print(f"\n[bold]Running full pipeline[/bold] for niche: [cyan]{niche}[/cyan]\n")

    flow = AdsFlow()
    flow.state.niche = niche
    result = flow.kickoff()

    logger.info("Flow complete. Summary:\n{}", result)
    console.print("\n[bold]Run Summary:[/bold]")
    try:
        summary = json.loads(result) if isinstance(result, str) else result
        _print_step_statuses(summary.get("step_statuses", {}))
    except Exception:
        console.print(str(result))


def _run_single_step(step: str, niche: str, settings) -> None:
    """Run only one specific pipeline step."""
    from agents import (
        build_ad_researcher, build_research_task,
        build_pain_extractor, build_extraction_task,
        build_script_writer, build_script_task,
        build_video_producer, build_production_task,
    )
    from crewai import Crew, Process

    step = step.lower()
    console.print(f"\n[bold]Running single step:[/bold] [cyan]{step}[/cyan]\n")

    if step == "research":
        agent = build_ad_researcher()
        task = build_research_task(agent)
    elif step == "extract":
        agent = build_pain_extractor()
        ads_path = settings.outputs_dir / "ads_raw.json"
        ads_json = ads_path.read_text("utf-8") if ads_path.exists() else "[]"
        task = build_extraction_task(agent)
        task.description = task.description.replace("{ads_data}", ads_json[:6000])
    elif step == "script":
        agent = build_script_writer()
        task = build_script_task(agent)
    elif step == "video":
        agent = build_video_producer()
        task = build_production_task(agent)
    else:
        console.print(f"[red]Unknown step: {step}. Use: research | extract | script | video[/red]")
        sys.exit(1)

    crew = Crew(agents=[agent], tasks=[task], process=Process.sequential, verbose=True)
    result = crew.kickoff()
    logger.success("Step '{}' complete", step)
    console.print(f"\n[green]✓ Step '{step}' complete.[/green]")
    console.print(str(result.raw if hasattr(result, "raw") else result)[:500])


def _validate_config(settings) -> None:
    """Check all required env vars are set."""
    issues = []

    checks = [
        ("GEMINI_API_KEY", settings.gemini_api_key, ""),
        ("OPENROUTER_API_KEY", settings.openrouter_api_key, "YOUR_OPENROUTER_API_KEY_HERE"),
        ("APIFY_API_TOKEN", settings.apify_api_token, "YOUR_APIFY_API_TOKEN_HERE"),
        ("ELEVENLABS_API_KEY", settings.elevenlabs_api_key, "YOUR_ELEVENLABS_API_KEY_HERE"),
        ("GDRIVE_FILE_ID", settings.gdrive_file_id, "YOUR_GOOGLE_DRIVE_FILE_ID_HERE"),
    ]

    table = Table(title="Configuration Check", show_header=True)
    table.add_column("Variable", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Value Preview")

    for name, value, placeholder in checks:
        if not value or value == placeholder:
            status = "[red]✗ MISSING[/red]"
            if name not in ("GEMINI_API_KEY", "GDRIVE_FILE_ID"):
                issues.append(name)
            preview = "[red]NOT SET[/red]"
        else:
            status = "[green]✓ SET[/green]"
            preview = value[:8] + "..." if len(value) > 8 else value

        table.add_row(name, status, preview)

    console.print(table)

    # Show active LLM provider
    if settings.gemini_api_key:
        console.print(
            f"\n[green]🧠 LLM Provider: Google Gemini ({settings.gemini_model})[/green]"
            f"\n[dim]   Free tier: ~1500 req/day, 15 RPM[/dim]"
        )
    elif settings.openrouter_api_key:
        console.print(
            f"\n[yellow]🧠 LLM Provider: OpenRouter ({settings.openrouter_model})[/yellow]"
            f"\n[dim]   Free tier: 50 req/day ⚠ (set GEMINI_API_KEY for 30x more)[/dim]"
        )
    else:
        console.print("\n[red]✗ No LLM provider configured! Set GEMINI_API_KEY or OPENROUTER_API_KEY.[/red]")
        issues.append("LLM_PROVIDER")

    if issues:
        console.print(
            f"\n[yellow]⚠ {len(issues)} variable(s) missing. "
            f"Copy .env.example to .env and fill in your keys.[/yellow]"
        )
        console.print(f"Missing: {', '.join(issues)}\n")


def _print_step_statuses(statuses: dict) -> None:
    table = Table(title="Step Results", show_header=True)
    table.add_column("Step", style="cyan")
    table.add_column("Status", style="bold")

    icons = {"success": "[green]✓ success[/green]", "failed": "[red]✗ failed[/red]"}
    for step, status in statuses.items():
        table.add_row(step, icons.get(status, status))

    console.print(table)


def _print_output_summary(settings) -> None:
    files = [
        ("ads_raw.json", settings.outputs_dir / "ads_raw.json"),
        ("pain_concepts.json", settings.outputs_dir / "pain_concepts.json"),
        ("ad_script.json", settings.outputs_dir / "ad_script.json"),
        ("voiceover.mp3", settings.outputs_dir / "audio" / "voiceover.mp3"),
        ("final_ad.mp4", settings.videos_dir / "final_ad.mp4"),
        ("run_summary.json", settings.outputs_dir / "run_summary.json"),
    ]

    table = Table(title="Output Files", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Exists", style="bold")
    table.add_column("Size")

    for name, path in files:
        exists = path.exists()
        size = f"{path.stat().st_size:,} bytes" if exists else "-"
        table.add_row(name, "[green]✓[/green]" if exists else "[dim]-[/dim]", size)

    console.print(table)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
