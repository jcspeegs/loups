"""Extract thumbnail images from video files using SSIM-based frame matching."""

import logging
from pathlib import Path
from typing import Callable, NamedTuple, Optional

import cv2 as cv
import numpy as np
from skimage.metrics import structural_similarity as ssim

from .frame_utils import calculate_frame_frequency

logger = logging.getLogger(__name__)


class ThumbnailResult(NamedTuple):
    """Holds the result of a thumbnail extraction operation."""

    success: bool
    frame_number: int
    timestamp_ms: float
    ssim_score: float
    output_path: Path


class ThumbnailExtractor:
    """Extract thumbnail frames from videos using SSIM-based template matching."""

    def __init__(
        self,
        video_path: Path,
        template_path: Optional[Path] = None,
        resolution: int = 3,
        scan_duration: int = 120,
        threshold: float = 0.8,
    ):
        """
        Initialize ThumbnailExtractor.

        Args:
            video_path: Path to video file
            template_path: Path to template image (uses default if None)
            resolution: Frames to check per second (matches Loups)
            scan_duration: Maximum seconds to scan from video start
            threshold: Minimum SSIM score to accept (0.0-1.0)
        """
        self.video_path = video_path
        self.template = load_template(template_path)
        self.resolution = resolution
        self.scan_duration = scan_duration
        self.threshold = threshold
        self.capture = cv.VideoCapture(str(video_path))
        self.frame_rate = self.capture.get(cv.CAP_PROP_FPS)

    def frame_frequency(self) -> int:
        """Get the number of frames to skip before processing a new frame."""
        return calculate_frame_frequency(self.frame_rate, self.resolution)


def get_default_thumbnail_template() -> Path:
    """Return path to bundled default thumbnail template."""
    return Path(__file__).parent / "data" / "thumbnail_template.png"


def load_template(template_path: Optional[Path] = None) -> np.ndarray:
    """
    Load thumbnail template, using default if not specified.

    Args:
        template_path: Path to template image (None for default)

    Returns:
        Template image as numpy array

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    if template_path is None:
        template_path = get_default_thumbnail_template()

    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    return cv.imread(str(template_path))


def generate_default_output_path(video_path: Path) -> Path:
    """
    Generate default thumbnail output path in current working directory.

    Args:
        video_path: Path to input video file

    Returns:
        Path to output thumbnail in cwd

    Examples:
        Input: '/path/to/game.mp4' → Output: './game-thumbnail.jpg'
        Input: 'softball.mp4' → Output: './softball-thumbnail.jpg'
    """
    stem = video_path.stem
    return Path.cwd() / f"{stem}-thumbnail.jpg"


def calculate_ssim(frame: np.ndarray, template: np.ndarray) -> float:
    """
    Calculate SSIM (Structural Similarity Index) between frame and template.

    Args:
        frame: Video frame as numpy array
        template: Template image as numpy array

    Returns:
        SSIM score (0.0 to 1.0, where 1.0 is perfect match)
    """
    # Resize frame to match template dimensions
    frame_resized = cv.resize(frame, (template.shape[1], template.shape[0]))

    # Convert to grayscale
    frame_gray = cv.cvtColor(frame_resized, cv.COLOR_BGR2GRAY)
    template_gray = cv.cvtColor(template, cv.COLOR_BGR2GRAY)

    # Calculate SSIM
    score = ssim(frame_gray, template_gray)
    return score


def extract_thumbnail(
    video_path: Path,
    template_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    threshold: float = 0.35,
    scan_duration: int = 120,
    resolution: int = 3,
    on_progress: Optional[Callable[[int, int], None]] = None,
    quiet: bool = False,
) -> Optional[ThumbnailResult]:
    """
    Extract first frame matching template above threshold.

    Core thumbnail extraction logic used by both CLI commands.
    Scans video from start, checking frames at specified resolution.
    Stops immediately when a frame exceeds the SSIM threshold.

    Args:
        video_path: Path to video file
        template_path: Path to template image (uses default if None)
        output_path: Where to save thumbnail (generates default in cwd if None)
        threshold: Minimum SSIM score to accept (0.0-1.0)
        scan_duration: Maximum seconds to scan from video start
        resolution: Frames to process per second
        on_progress: Optional callback for progress updates
        quiet: Suppress output

    Returns:
        ThumbnailResult on success, None if no frame exceeds threshold
    """
    extractor = ThumbnailExtractor(
        video_path=video_path,
        template_path=template_path,
        resolution=resolution,
        scan_duration=scan_duration,
        threshold=threshold,
    )

    max_frames = int(scan_duration * extractor.frame_rate)
    frame_interval = extractor.frame_frequency()

    logger.debug(
        f"Scanning {video_path.name}: max_frames={max_frames}, "
        f"frame_interval={frame_interval}, threshold={threshold}"
    )

    frame_count = 0
    frames_checked = 0

    while frame_count < max_frames:
        ret = extractor.capture.grab()
        if not ret:
            break

        frame_count += 1

        # Sample at interval (same pattern as Loups.scan())
        if frame_count % frame_interval != 0:
            continue

        ret, frame = extractor.capture.retrieve()
        if not ret:
            break

        frames_checked += 1
        score = calculate_ssim(frame, extractor.template)

        logger.debug(f"Frame {frame_count}: SSIM score = {score:.4f}")

        # Call progress callback if provided
        if on_progress and not quiet:
            on_progress(frame_count, max_frames)

        # First frame above threshold wins!
        if score >= threshold:
            output = output_path or generate_default_output_path(video_path)
            cv.imwrite(str(output), frame)
            timestamp = extractor.capture.get(cv.CAP_PROP_POS_MSEC)

            logger.info(
                f"Thumbnail extracted: frame={frame_count}, "
                f"timestamp={timestamp:.0f}ms, score={score:.4f}, path={output}"
            )

            return ThumbnailResult(
                success=True,
                frame_number=frame_count,
                timestamp_ms=timestamp,
                ssim_score=score,
                output_path=output,
            )

    # No match found - log warning and return None
    logger.warning(
        f"No frame exceeded threshold {threshold} "
        f"within {scan_duration}s (checked {frames_checked} frames)"
    )
    return None
