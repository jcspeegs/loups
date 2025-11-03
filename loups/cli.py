"""Command-line interface for the loups package."""

import logging
import sys
import threading
import time
from importlib.resources import files
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.text import Text

from loups import Loups

app = typer.Typer(
    help="Scan Lights Out HB fastpitch game videos to extract batter information."
)
console = Console()
err_console = Console(stderr=True)


def get_default_template() -> Path:
    """Get the path to the default bundled template."""
    try:
        # Use importlib.resources to locate the bundled template
        template_path = files("loups").joinpath("data/template_solid.png")
        # For Python 3.9+, we need to use as_file context manager
        # but for simpler usage, we'll convert to string path
        return Path(str(template_path))
    except Exception:
        # Fallback for development/testing
        fallback = Path(__file__).parent / "data" / "template_solid.png"
        if fallback.exists():
            return fallback
        raise FileNotFoundError(
            "Could not locate default template. "
            "Please specify a template with --template"
        )


def setup_logging(
    log_path: Optional[Path] = None, quiet: bool = False, debug: bool = False
) -> None:
    """Set up logging with rotation."""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Create rotating file handler if log_path is provided
    if log_path is not None:
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
        )
        # Set file log level based on debug flag
        file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Always log errors to stderr (even in quiet mode)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)


def format_elapsed_time(seconds: float) -> str:
    """Format elapsed time as HH:MM:SS."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def create_progress_display(
    elapsed: float,
    batter_count: int,
    spinner_state: int,
    percent: Optional[float] = None,
    last_batter: Optional[str] = None,
) -> Text:
    """Create the animated progress display with baseball emojis."""
    # Softball moving left and right (bouncing animation)
    positions = ["🥎   ", " 🥎  ", "  🥎 ", "   🥎", "  🥎 ", " 🥎  "]
    softball_display = positions[spinner_state % len(positions)]

    # Build the display text
    text = Text()
    text.append(softball_display, style="bold yellow")
    text.append(" Scanning... ", style="bold")

    # Show percentage if available
    if percent is not None:
        text.append(f"{percent:.1f}%", style="bold cyan")
        text.append(" | ", style="dim")

    text.append("Found ", style="dim")
    text.append(f"{batter_count}", style="bold green")
    text.append(f" batter{'s' if batter_count != 1 else ''}", style="dim")

    # Show last batter found
    if last_batter:
        text.append("\n")
        text.append("🏟️     Found: ", style="dim")
        text.append(last_batter, style="bold green")

    return text


@app.command()
def main(
    video: Path = typer.Argument(  # noqa: B008
        ...,
        exists=True,
        help="Path to the video file to scan",
    ),
    template: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--template",
        "-t",
        help="Path to template image (defaults to bundled template)",
    ),
    log: Optional[str] = typer.Option(  # noqa: B008
        None,
        "--log",
        "-l",
        is_flag=False,
        flag_value="loups.log",
        help=(
            "Enable logging. Use without argument for default 'loups.log', "
            "or provide a path for custom location. "
            "Logs rotate at 10MB, keeps 3 backups."
        ),
    ),
    output: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Save results to file (YouTube chapter format)",
    ),
    quiet: bool = typer.Option(  # noqa: B008
        False,
        "--quiet",
        "-q",
        help="Suppress stdout output (errors still go to stderr)",
    ),
    debug: bool = typer.Option(  # noqa: B008
        False,
        "--debug",
        "-d",
        help="Enable DEBUG level logging to file (default is INFO)",
    ),
) -> None:
    """Scan a Lights Out HB fastpitch game video and extract batter timestamps."""
    # Determine log path
    if log is not None:
        log_path = Path(log)
    else:
        log_path = None

    # Set up logging
    setup_logging(log_path, quiet, debug)

    # Get template path
    if template is None:
        try:
            template = get_default_template()
        except FileNotFoundError as e:
            err_console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    # Verify template exists
    if not template.exists():
        err_console.print(f"[red]Error:[/red] Template file not found: {template}")
        raise typer.Exit(1)

    # Progress tracking
    start_time = time.time()
    batter_count = 0
    spinner_state = 0
    last_batter_name = None
    progress_percent = 0.0

    def on_batter_found(batter_info):
        """Handle callback when a new batter is found."""
        nonlocal batter_count, last_batter_name
        batter_count += 1
        last_batter_name = batter_info.batter_name

    def on_progress(frames_processed, total_frames):
        """Update progress percentage on each frame processed."""
        nonlocal progress_percent
        if total_frames > 0:
            progress_percent = (frames_processed / total_frames) * 100

    # Initialize Loups with callback
    try:
        game = Loups(
            str(video),
            str(template),
            on_batter_found=on_batter_found,
            on_progress=on_progress,
        )
    except Exception as e:
        err_console.print(f"[red]Error:[/red] Failed to initialize scanner: {e}")
        raise typer.Exit(1)

    # Run scan with progress display
    if not quiet:
        console.print(f"[bold]Scanning video:[/bold] {video}")
        console.print()

        # Variables to track scan completion and errors
        scan_complete = threading.Event()
        scan_error = None

        def run_scan():
            """Run the scan in a background thread."""
            nonlocal scan_error
            try:
                game.scan()
            except Exception as e:
                scan_error = e
            finally:
                scan_complete.set()

        # Start scan in background thread
        scan_thread = threading.Thread(target=run_scan, daemon=True)
        scan_thread.start()

        with Live(
            create_progress_display(0, 0, 0, 0.0),
            refresh_per_second=4,
            console=console,
        ) as live:
            # Continuously update display while scan is running
            while not scan_complete.is_set():
                current_time = time.time()
                elapsed = current_time - start_time
                spinner_state += 1
                live.update(
                    create_progress_display(
                        elapsed,
                        batter_count,
                        spinner_state,
                        progress_percent,
                        last_batter_name,
                    )
                )
                time.sleep(0.25)  # Update every 250ms

            # Final update
            elapsed = time.time() - start_time
            live.update(
                create_progress_display(
                    elapsed,
                    batter_count,
                    spinner_state,
                    progress_percent,
                    last_batter_name,
                )
            )

        # Check for errors
        if scan_error:
            err_console.print(f"\n[red]Error:[/red] Scan failed: {scan_error}")
            raise typer.Exit(1)

        console.print()
        console.print(
            f"🏆 [bold green]Scan complete![/bold green] "
            f"Found {game.batter_count} batters "
            f"in {format_elapsed_time(elapsed)}"
        )
        console.print()
    else:
        # Quiet mode - just run the scan
        try:
            game.scan()
        except Exception as e:
            err_console.print(f"[red]Error:[/red] Scan failed: {e}")
            raise typer.Exit(1)

    # Get results using the display() method
    results = game.batters.display()

    # Output to stdout (unless quiet)
    if not quiet:
        console.print("[bold]YouTube Chapters:[/bold]")
        console.print(results)

    # Output to file if specified
    if output:
        try:
            output.write_text(results)
            if not quiet:
                console.print()
                console.print(f"✓ Results saved to: [cyan]{output}[/cyan]")
        except Exception as e:
            err_console.print(f"[red]Error:[/red] Failed to write output file: {e}")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
