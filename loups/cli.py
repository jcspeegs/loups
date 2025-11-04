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
from loups.thumbnail_extractor import extract_thumbnail

app = typer.Typer(
    help="Scan Lights Out HB fastpitch game videos to extract batter information.",
    invoke_without_command=True,
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


def get_default_thumbnail_template() -> Path:
    """Get the path to the default bundled thumbnail template."""
    try:
        # Use importlib.resources to locate the bundled thumbnail template
        template_path = files("loups").joinpath("data/thumbnail_template.png")
        return Path(str(template_path))
    except Exception:
        # Fallback for development/testing
        fallback = Path(__file__).parent / "data" / "thumbnail_template.png"
        if fallback.exists():
            return fallback
        raise FileNotFoundError(
            "Could not locate default thumbnail template. "
            "Please specify a template with --thumbnail-template or "
            "add thumbnail_template.png to loups/data/"
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
    text.append(" Scanning batters... ", style="bold")

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


def create_thumbnail_progress_display(
    spinner_state: int,
) -> Text:
    """Create the animated progress display for thumbnail extraction."""
    positions = ["🥎   ", " 🥎  ", "  🥎 ", "   🥎", "  🥎 ", " 🥎  "]
    softball_display = positions[spinner_state % len(positions)]

    text = Text()
    text.append(softball_display, style="bold yellow")
    text.append(" Extracting thumbnail...", style="bold")
    return text


def _detect_piped_output() -> bool:
    """Check if stdout is being piped/redirected."""
    return not sys.stdout.isatty()


def _calculate_show_progress(quiet: bool, is_piped: bool) -> bool:
    """Determine if progress should be shown based on quiet and piped state."""
    return not quiet and not is_piped


def _run_thumbnail_extraction(
    video: Path,
    template: Optional[Path],
    output: Optional[Path],
    threshold: float,
    scan_duration: int,
    frames_per_second: int,
    quiet: bool,
    is_fatal_on_error: bool = True,
    show_header: bool = True,
) -> Optional:
    """
    Unified thumbnail extraction with configurable behavior.

    Args:
        video: Path to video file
        template: Path to thumbnail template (None = use default)
        output: Path for output thumbnail (None = auto-generate)
        threshold: Minimum SSIM score (0.0-1.0)
        scan_duration: Maximum seconds to scan
        frames_per_second: Frame sampling rate
        quiet: Suppress output
        is_fatal_on_error: If True, exit on errors; if False, warn and return None
        show_header: If True, show "Scanning video:" header

    Returns:
        ThumbnailResult on success, None on failure (when not fatal)
    """
    is_piped = _detect_piped_output()
    show_progress = _calculate_show_progress(quiet, is_piped)

    # Show "Scanning video:" header if requested
    if show_header and show_progress:
        console.print(f"[bold]Scanning video:[/bold] {video}")
        console.print()

    # Resolve template path
    thumb_template = template
    if thumb_template is None:
        try:
            thumb_template = get_default_thumbnail_template()
        except FileNotFoundError as e:
            if is_fatal_on_error:
                err_console.print(f"[red]Error:[/red] {e}")
                raise typer.Exit(1)
            else:
                err_console.print(f"[yellow]Warning:[/yellow] {e}")
                err_console.print("[yellow]Skipping thumbnail extraction.[/yellow]")
                return None

    # Verify template exists
    if not thumb_template.exists():
        error_msg = f"Thumbnail template not found: {thumb_template}"
        if is_fatal_on_error:
            err_console.print(f"[red]Error:[/red] {error_msg}")
            raise typer.Exit(1)
        else:
            err_console.print(f"[yellow]Warning:[/yellow] {error_msg}")
            err_console.print("[yellow]Skipping thumbnail extraction.[/yellow]")
            return None

    # Perform extraction
    result = None
    extraction_error = None

    try:
        if show_progress:
            # Show animated progress display
            extraction_complete = threading.Event()
            spinner_state = 0

            def run_extraction():
                """Run extraction in background thread."""
                nonlocal result, extraction_error
                try:
                    nonlocal_result = extract_thumbnail(
                        video_path=video,
                        template_path=thumb_template,
                        output_path=output,
                        threshold=threshold,
                        scan_duration=scan_duration,
                        resolution=frames_per_second,
                        quiet=True,  # Suppress internal output during animation
                    )
                    result = nonlocal_result
                except Exception as e:
                    extraction_error = e
                finally:
                    extraction_complete.set()

            # Start extraction in background thread
            extraction_thread = threading.Thread(target=run_extraction, daemon=True)
            extraction_thread.start()

            # Show animated progress while extracting
            with Live(
                create_thumbnail_progress_display(0),
                refresh_per_second=4,
                console=console,
            ) as live:
                while not extraction_complete.is_set():
                    spinner_state += 1
                    live.update(create_thumbnail_progress_display(spinner_state))
                    time.sleep(0.25)  # Update every 250ms

            # Check for errors
            if extraction_error:
                raise extraction_error

        else:
            # Direct call without animation (quiet or piped output)
            result = extract_thumbnail(
                video_path=video,
                template_path=thumb_template,
                output_path=output,
                threshold=threshold,
                scan_duration=scan_duration,
                resolution=frames_per_second,
                quiet=quiet,
            )

    except Exception as e:
        error_msg = f"Failed to extract thumbnail: {e}"
        if is_fatal_on_error:
            err_console.print(f"[red]Error:[/red] {error_msg}")
            raise typer.Exit(1)
        else:
            err_console.print(f"[yellow]Warning:[/yellow] {error_msg}")
            err_console.print("[yellow]Continuing without thumbnail.[/yellow]")
            return None

    # Handle result
    if result is None:
        warning_msg = (
            f"No frame exceeded threshold {threshold} " f"within {scan_duration}s"
        )
        if is_fatal_on_error:
            if not quiet:
                err_console.print(f"[yellow]Warning:[/yellow] {warning_msg}")
            raise typer.Exit(1)
        else:
            if show_progress:
                console.print(f"[yellow]⚠ {warning_msg}[/yellow]")
            return None

    # Display result
    if show_progress:
        # Show success message with details
        console.print(
            f"✓ [bold green]Thumbnail extracted![/bold green]\n"
            f"  Timestamp: {result.timestamp_ms:.0f}ms\n"
            f"  SSIM Score: {result.ssim_score:.4f}\n"
            f"  Saved to: [cyan]{result.output_path}[/cyan]"
        )
    elif not quiet and is_piped:
        # For piped output, just print the path
        print(str(result.output_path))

    return result


@app.command()
def thumbnail(
    ctx: typer.Context,
    thumbnail_template: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--thumbnail-template",
        help="Path to thumbnail template image (defaults to bundled template)",
    ),
    thumbnail_output: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--thumbnail-output",
        help="Output path for thumbnail (default: <video>-thumbnail.jpg in cwd)",
    ),
    thumbnail_scan_duration: int = typer.Option(  # noqa: B008
        120,
        "--thumbnail-scan-duration",
        help="Maximum seconds to scan from video start",
    ),
    thumbnail_threshold: float = typer.Option(  # noqa: B008
        0.35,
        "--thumbnail-threshold",
        min=0.0,
        max=1.0,
        help="Minimum SSIM score to accept (0.0-1.0)",
    ),
    thumbnail_frames_per_second: int = typer.Option(  # noqa: B008
        3,
        "--thumbnail-frames-per-second",
        min=1,
        help="Frame sampling rate (frames to check per second)",
    ),
    quiet: bool = typer.Option(  # noqa: B008
        False,
        "--quiet",
        "-q",
        help="Suppress progress display and output",
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
    debug: bool = typer.Option(  # noqa: B008
        False,
        "--debug",
        "-d",
        help="Enable DEBUG level logging to file (default is INFO)",
    ),
) -> None:
    """Extract thumbnail from video using SSIM-based template matching."""
    # Get video from parent context
    video = ctx.parent.params["video"]
    # Ensure video is a Path object (defensive programming)
    if not isinstance(video, Path):
        video = Path(video)

    # Set up logging
    if log is not None:
        log_path = Path(log)
    else:
        log_path = None
    setup_logging(log_path, quiet, debug)

    # Use shared helper function with fatal error handling
    _run_thumbnail_extraction(
        video=video,
        template=thumbnail_template,
        output=thumbnail_output,
        threshold=thumbnail_threshold,
        scan_duration=thumbnail_scan_duration,
        frames_per_second=thumbnail_frames_per_second,
        quiet=quiet,
        is_fatal_on_error=True,  # Exit on errors (standalone command)
    )


@app.callback()
def callback(
    ctx: typer.Context,
    video: Path = typer.Argument(  # noqa: B008
        ...,
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
        help="Suppress progress display and output (errors still go to stderr)",
    ),
    debug: bool = typer.Option(  # noqa: B008
        False,
        "--debug",
        "-d",
        help="Enable DEBUG level logging to file (default is INFO)",
    ),
    extract_thumbnail: bool = typer.Option(  # noqa: B008
        False,
        "--extract-thumbnail",
        help="Extract thumbnail during chapter scan",
    ),
    thumbnail_template: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--thumbnail-template",
        help="Path to thumbnail template (defaults to bundled template)",
    ),
    thumbnail_output: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--thumbnail-output",
        help="Output path for thumbnail (default: <video>-thumbnail.jpg in cwd)",
    ),
    thumbnail_threshold: float = typer.Option(  # noqa: B008
        0.35,
        "--thumbnail-threshold",
        min=0.0,
        max=1.0,
        help="Minimum SSIM score for thumbnail (0.0-1.0)",
    ),
    thumbnail_scan_duration: int = typer.Option(  # noqa: B008
        120,
        "--thumbnail-scan-duration",
        help="Maximum seconds to scan for thumbnail",
    ),
    thumbnail_frames_per_second: int = typer.Option(  # noqa: B008
        3,
        "--thumbnail-frames-per-second",
        min=1,
        help="Frame sampling rate for thumbnail extraction",
    ),
) -> None:
    """
    Scan Lights Out HB fastpitch game videos to extract batter information.

    By default, scans a video for batters.
    Use 'thumbnail' command to extract thumbnails.
    """
    # If a subcommand was invoked, let it run
    if ctx.invoked_subcommand is not None:
        return

    # No subcommand - run the default scan behavior
    # Verify video exists
    if not video.exists():
        err_console.print(f"[red]Error:[/red] Video file not found: {video}")
        raise typer.Exit(1)

    # Determine log path
    if log is not None:
        log_path = Path(log)
    else:
        log_path = None

    # Set up logging
    setup_logging(log_path, quiet, debug)

    # Detect if stdout is being piped/redirected
    is_piped = not sys.stdout.isatty()

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

    # Show "Scanning video:" header at the top
    show_progress = not quiet and not is_piped
    if show_progress:
        console.print(f"[bold]Scanning video:[/bold] {video}")
        console.print()

    # Extract thumbnail if requested
    if extract_thumbnail:
        # Use shared helper function with non-fatal error handling
        _run_thumbnail_extraction(
            video=video,
            template=thumbnail_template,
            output=thumbnail_output,
            threshold=thumbnail_threshold,
            scan_duration=thumbnail_scan_duration,
            frames_per_second=thumbnail_frames_per_second,
            quiet=quiet,
            is_fatal_on_error=False,  # Warnings only, continue on errors
            show_header=False,  # Header already shown above
        )

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

    # Run scan with progress display (disabled when piped or quiet)
    if show_progress:
        # Add separator if we just extracted a thumbnail
        if extract_thumbnail:
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
        # Quiet mode or piped output - just run the scan
        try:
            game.scan()
        except Exception as e:
            err_console.print(f"[red]Error:[/red] Scan failed: {e}")
            raise typer.Exit(1)

    # Get results using the display() method
    results = game.batters.display()

    # Output to stdout (unless quiet)
    if not quiet:
        if is_piped:
            # When piped, output plain text to stdout (no formatting)
            print(results)
        else:
            # Interactive terminal: show formatted output
            console.print("[bold]YouTube Chapters:[/bold]")
            console.print(results)

    # Output to file if specified
    if output:
        try:
            output.write_text(results)
            if show_progress:
                console.print()
                console.print(f"✓ Results saved to: [cyan]{output}[/cyan]")
        except Exception as e:
            err_console.print(f"[red]Error:[/red] Failed to write output file: {e}")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
