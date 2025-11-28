"""Video scanner for extracting batter information using template matching and OCR.

This module provides the core Loups class for scanning videos to detect
batter at-bats or similar events. Originally designed for Lights Out HB
fastpitch softball games, but works with any video containing consistent
identifying frames.

Key Features:
    * Template-based frame detection using OpenCV
    * OCR text extraction for batter names and jersey numbers
    * YouTube chapter timestamp generation
    * Configurable frame sampling for performance
    * Progress callbacks for UI integration

Example:
    ```python
    from loups import Loups

    # Scan a video
    game = Loups("game.mp4", "template.png")
    game.scan()

    # Print YouTube chapters
    print(game.batters)
    print(f"Found {game.batter_count} batters")
    ```
"""

import logging
import re
from datetime import timedelta
from pathlib import Path
from typing import Callable, NamedTuple, Optional, Union

import cv2 as cv
import easyocr
import numpy as np

from .geometry import Point, Size
from .match_template_scan import MatchTemplateScan

logger = logging.getLogger(__name__)


class MilliSecond(float):
    """Custom millisecond type with YouTube chapter formatting.

    A float subclass that formats time values as YouTube-compatible chapter
    timestamps (MM:SS or HH:MM:SS format).
    """

    def __new__(cls, value):
        """Create a new MilliSecond instance.

        Args:
            value: Time value in milliseconds.

        Returns:
            New MilliSecond instance.

        Raises:
            ValueError: If value is negative.
        """
        if value < 0:
            raise ValueError(
                f"MilliSecond cannot be {value}, " "it must be a non-negative number."
            )
        return super().__new__(cls, value)

    def __str__(self):
        """Convert to string using YouTube chapter format.

        Returns:
            Formatted timestamp string (MM:SS or HH:MM:SS).
        """
        return self.yt_format()

    def yt_format(self) -> str:
        """Format milliseconds as YouTube chapter timestamp.

        Returns:
            Timestamp in MM:SS format (or HH:MM:SS if >= 1 hour).

        Examples:
            ```python
            ms = MilliSecond(65000)  # 65 seconds
            print(ms.yt_format())  # "01:05"

            ms = MilliSecond(3665000)  # 1 hour, 1 minute, 5 seconds
            print(ms.yt_format())  # "01:01:05"
            ```
        """
        td = timedelta(milliseconds=self)

        hours = td // timedelta(hours=1)
        minutes = td // timedelta(minutes=1) % 60
        seconds = td // timedelta(seconds=1) % 60

        return (
            f"{minutes:02.0f}:{seconds:02.0f}"
            if hours == 0
            else f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"
        )


class FrameBatterInfo(NamedTuple):
    """Batter information extracted from a single video frame.

    Attributes:
        ms: Timestamp of the frame in milliseconds.
        match_score: Template matching confidence score (0.0-1.0).
        is_batter: Whether a batter was detected in this frame.
        new_batter: Whether this is a new batter (transition from previous frame).
        batter_name: Name and jersey number extracted via OCR, or empty string.
    """

    ms: MilliSecond
    match_score: float
    is_batter: bool
    new_batter: bool
    batter_name: str


class BatterInfo(list[FrameBatterInfo]):
    """Collection of detected batters formatted for YouTube chapters.

    A list subclass containing FrameBatterInfo objects that can be formatted
    as YouTube-compatible chapter markers.
    """

    def __str__(self):
        """Convert to YouTube chapter format.

        Returns:
            Multi-line string with YouTube chapter timestamps and names.
        """
        return self.display()

    def display(self) -> str:
        """Format batter information as YouTube video chapters.

        Ensures YouTube chapter requirements are met:
        - First chapter begins at 00:00
        - Chapters are at least 10s apart
        - If first batter appears within 10s, timestamp is moved to 00:00

        Returns:
            Multi-line string with format "HH:MM:SS Name" per line.

        Examples:
            ```python
            batters = BatterInfo([
                FrameBatterInfo(
                    MilliSecond(15000), 0.95, True, True, "Sarah Johnson #7"
                ),
                FrameBatterInfo(
                    MilliSecond(45000), 0.93, True, True, "Emma Martinez #12"
                )
            ])
            print(batters.display())
            # 00:00 Game Time
            # 00:15 Sarah Johnson #7
            # 00:45 Emma Martinez #12
            ```
        """
        # TODO: Must be at least 3 chapters
        # TODO: If two batters up within < 10s then combine their names
        logger.debug(f"{self[0]=}")

        time_before_first_batter = timedelta(milliseconds=self[0].ms)
        logger.debug(f"{time_before_first_batter=}")
        need_intro_chapter = time_before_first_batter > timedelta(seconds=10)
        logger.debug(f"{need_intro_chapter=}")

        if need_intro_chapter is True:
            intro_title = "Game Time"
            intro_chapter = FrameBatterInfo(
                ms=MilliSecond(0.0),
                match_score=None,
                is_batter=False,
                new_batter=False,
                batter_name=intro_title,
            )
            self.insert(0, intro_chapter)
        elif need_intro_chapter is False:
            self[0] = self[0]._replace(ms=MilliSecond(0.0))
        logger.debug(f"{self[:1]=}")

        return "\n".join(
            [" ".join([str(frame.ms), frame.batter_name]) for frame in self]
        )


class Loups:
    """Extract batter information from Lights Out HB fastpitch videos."""

    _reader = None

    def __init__(
        self,
        scannable: Union[str, Path],
        template: Union[str, Path],
        method: str = "TM_CCOEFF_NORMED",
        threshold: Optional[float] = None,
        resolution: int = 3,
        on_batter_found: Optional[Callable[[FrameBatterInfo], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Initialize Loups video scanner.

        Args:
            scannable: Path to video file to scan.
            template: Path to template image used to identify batters.
            method: Template matching method (TM_SQDIFF, TM_SQDIFF_NORMED,
                TM_CCORR, TM_CCORR_NORMED, TM_CCOEFF, TM_CCOEFF_NORMED).
                Default: TM_CCOEFF_NORMED.
            threshold: Confidence threshold for accepting matches (0.0-1.0).
                Default varies by method.
            resolution: Number of frames to analyze per second. Default: 3.
            on_batter_found: Optional callback when batter is found.
                Signature: callback(batter_info: FrameBatterInfo) -> None
            on_progress: Optional callback for progress updates.
                Signature: callback(frames_processed: int, total_frames: int) -> None

        Examples:
            ```python
            # Scan a video
            game = Loups("game.mp4", "template.png")
            game.scan()
            print(game.batters)
            print(f"Found {game.batter_count} batters")

            # With callbacks
            def on_found(batter_info):
                print(f"Found: {batter_info.batter_name}")

            game = Loups("game.mp4", "template.png", on_batter_found=on_found)
            ```
        """
        self._scannable = scannable
        self._capture = self.create_capture()
        self._frame_rate = self.get_frame_rate()
        self.template = template
        self._method = method
        self.resolution = resolution
        self.search_quadrant = "bottomleft"
        self.on_batter_found = on_batter_found
        self.on_progress = on_progress

    @property
    def method(self) -> str:
        """Get the template matching method name.

        Returns:
            Template matching method string (e.g., "TM_CCOEFF_NORMED").
        """
        return self._method

    @property
    def scannable(self) -> Union[str, Path]:
        """Get the path to the video file being scanned.

        Returns:
            Path to the video file.
        """
        return self._scannable

    @property
    def capture(self) -> cv.VideoCapture:
        """Get the OpenCV VideoCapture object.

        Returns:
            cv.VideoCapture instance for the video file.
        """
        return self._capture

    @property
    def total_frames(self) -> float:
        """Get total number of frames in the video.

        Returns:
            Total frame count.
        """
        return self.capture.get(cv.CAP_PROP_FRAME_COUNT)

    @property
    def frame_rate(self) -> float:
        """Get the frame rate of the video.

        Returns:
            Frame rate in frames per second (fps).
        """
        return self._frame_rate

    @property
    def template(self) -> np.ndarray:
        """Get the template image as a numpy array.

        Returns:
            Grayscale template image as numpy ndarray.
        """
        return self._template

    @template.setter
    def template(self, value):
        """Set the template image from file path.

        Args:
            value: Path to template image file.
        """
        self._template = cv.imread(value, cv.IMREAD_GRAYSCALE)

    @classmethod
    def get_reader(cls) -> easyocr.Reader:
        """Get or initialize the shared EasyOCR reader.

        Lazy initialization pattern to avoid loading OCR models until needed.

        Returns:
            Initialized easyocr.Reader instance for English text.
        """
        return easyocr.Reader(["en"]) if cls._reader is None else cls._reader

    def create_capture(self) -> cv.VideoCapture:
        """Create OpenCV VideoCapture for the video file.

        Returns:
            cv.VideoCapture object for reading video frames.
        """
        return cv.VideoCapture(self.scannable)

    def get_frame_rate(self) -> float:
        """Get frame rate from video capture.

        Uses OpenCV CAP_PROP_FPS property.

        Returns:
            Frame rate in frames per second.

        Note:
            See https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html
        """
        return self.capture.get(5)

    def frame_frequency(self) -> int:
        """Calculate frame sampling interval based on resolution.

        Returns:
            Number of frames to skip between samples (e.g., 10 means every 10th frame).
        """
        from .frame_utils import calculate_frame_frequency

        return calculate_frame_frequency(self.frame_rate, self.resolution)

    def timestamp(self) -> float:
        """Get current video position timestamp.

        Returns:
            Current timestamp in milliseconds.
        """
        return self.capture.get(0)

    def match_template_scan(self) -> MatchTemplateScan:
        """Perform template matching on current frame.

        Returns:
            MatchTemplateScan object containing match results.
        """
        scan = MatchTemplateScan(
            image=cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY),
            template=self.template,
            method=self.method,
        )
        return scan

    def new_batter(
        self, res: list[FrameBatterInfo], ms: float, threshold: int = 2000
    ) -> bool:
        """Determine if a frame contains a new batter.

        Args:
            res: List of previous FrameBatterInfo results.
            ms: Current frame timestamp in milliseconds.
            threshold: Minimum time in milliseconds between new batters.

        Returns:
            True if this frame represents a new batter, False otherwise.
        """
        new_batter_frame = self.prev_frame_is_not_batter(res)
        logger.debug(f"{new_batter_frame=}")

        prev_batter_frame_timestamp = self.prev_batter_frame_timestamp(res)
        try:
            time_since_prev_batter_frame = ms - prev_batter_frame_timestamp
        except TypeError:
            time_since_prev_batter_frame = None

        return (
            new_batter_frame and time_since_prev_batter_frame > threshold
            if time_since_prev_batter_frame is not None
            else new_batter_frame
        )

    def prev_batter_frame_timestamp(
        self, frames: list[FrameBatterInfo]
    ) -> Optional[int]:
        """Get timestamp of the most recent frame containing a batter.

        Args:
            frames: List of FrameBatterInfo objects to search.

        Returns:
            Timestamp in milliseconds of the last batter frame, or None
            if no batters found.
        """
        try:
            ts = max(frame.ms for frame in frames if frame.is_batter)
        except ValueError:
            ts = None
        return ts

    @staticmethod
    def prev_frame_is_not_batter(res: list) -> bool:
        """Check if the previous frame did not contain a batter.

        Args:
            res: List of FrameBatterInfo results.

        Returns:
            True if previous frame had no batter, False otherwise.
        """
        try:
            prev_frame_is_batter = res[-1].is_batter
        except IndexError:
            prev_frame_is_batter = False
        return not prev_frame_is_batter

    def batter_name(self, match_top_left: Point, threshold: float = 0.2) -> str:
        """Extract batter name from frame using OCR.

        Args:
            match_top_left: Top-left corner of template match location.
            threshold: Minimum OCR confidence score to accept text
                (0.0-1.0).

        Returns:
            Extracted batter name with jersey number, or empty string if no text found.

        Examples:
            ```python
            name = game.batter_name(Point(100, 200))
            # Returns: "Sarah Johnson #7"
            ```
        """
        template_size = Size(*self.template.shape)

        match_bottom_right = Point(
            match_top_left.x + template_size.width,
            match_top_left.y + template_size.height,
        )

        # Do not scan the template headshot
        headshot = Size(width=215, height=None)

        image_to_scan = self.frame[
            match_top_left.y : match_bottom_right.y,
            match_top_left.x + headshot.width : match_bottom_right.x,
        ]

        # Extract text
        ocr = self.get_reader().readtext(image_to_scan)
        logger.debug(f"{ocr=}")

        # Filter by confidence threshold
        filtered_ocr = [
            (location, text, score)
            for location, text, score in ocr
            if score > threshold
        ]

        # Sort by x-coordinate (left-to-right) using the leftmost point
        # OCR location can be:
        # - [[top-left], [top-right], [bottom-right], [bottom-left]]
        #   (list of points)
        # - (x1, y1, x2, y2) (tuple of coordinates)
        # For left-to-right reading, sort by x-coordinate of leftmost point
        def get_leftmost_x(item):
            location = item[0]
            # Check if it's a list of points or a flat tuple
            if isinstance(location[0], (list, tuple)) and len(location[0]) >= 2:
                # List of points: [[x1, y1], [x2, y2], ...]
                return min(point[0] for point in location)
            else:
                # Flat tuple: (x1, y1, x2, y2)
                # x-coordinates are at even indices
                return min(location[i] for i in range(0, len(location), 2))

        sorted_ocr = sorted(filtered_ocr, key=get_leftmost_x)

        # Extract just the text strings after sorting
        text = [text for location, text, score in sorted_ocr]

        # Extract jersey numbers and name parts from all elements
        jersey_pattern = r"#\d+"

        # Collect all jersey numbers from all text elements
        # (now in left-to-right order)
        all_jerseys = [
            jersey for item in text for jersey in re.findall(jersey_pattern, item)
        ]

        # Collect all non-jersey text parts
        # (remove jerseys, normalize spaces, preserve left-to-right order)
        all_name_parts = [
            re.sub(r"\s+", " ", re.sub(jersey_pattern, "", item).strip())
            for item in text
        ]

        # Filter out empty strings
        all_name_parts = [part for part in all_name_parts if part]

        # Combine: name parts first (in left-to-right order), then jersey numbers
        result = " ".join(all_name_parts + all_jerseys)
        logger.debug(
            f"text={text}, all_name_parts={all_name_parts}, "
            f"all_jerseys={all_jerseys}, result={result}"
        )

        return result

    # def preprocess_frame(self):
    # self.logger.debug(f"{frame.shape[:2]=}")
    # frame_size = Size(*frame.shape[:2])
    # self.logger.debug(f"{frame_size=}")
    # match self.search_quadrant:
    #     case "bottomleft":
    #         y = 0.5 * frame_size.height, frame_size.height
    #         x = 0, frame_size.width
    # self.logger.debug(f"{x=}")
    # self.logger.debug(f"{y=}")
    # # cropped_frame = frame[y_start:y_end, x_start:x_end]
    # return self.frame

    def scan(self) -> "Loups":
        """Scan the video file to detect batters and extract information.

        Process video frames at the specified resolution, perform template matching,
        and use OCR to extract batter names. Results are stored in the `batters`
        attribute.

        Returns:
            Self (for method chaining).

        Examples:
            ```python
            game = Loups("video.mp4", "template.png")
            game.scan()
            print(f"Found {game.batter_count} batters")
            print(game.batters)
            ```
        """
        frame_count = 0

        # Initalize a list to collect FrameBatterInfo objects
        frames = []
        while True:
            ret = self.capture.grab()

            if not ret:
                break

            frame_count += 1
            logger.debug(f"{frame_count=}")
            frame_frequency = self.frame_frequency()
            keep_frame = frame_count % frame_frequency == 0
            logger.debug(f"{keep_frame=}")

            if keep_frame:
                ret, self.frame = self.capture.retrieve()
                # self.frame = self.preprocess_frame()

                # Record timestamp of frame
                ms = MilliSecond(self.timestamp())

                # Search for template in frame
                is_match, score, match_top_left = self.match_template_scan().result

                # Does this frame contain a new batter
                new_batter = self.new_batter(frames, ms) if is_match else False
                new_batter_name = (
                    self.batter_name(match_top_left) if new_batter else None
                )

                frame_batter_info = FrameBatterInfo(
                    ms=ms,
                    match_score=score,
                    is_batter=is_match,
                    new_batter=new_batter,
                    batter_name=new_batter_name,
                )
                logger.info(f"{frame_batter_info=}")
                frames.append(frame_batter_info)

                # Call callback if a new batter was found
                if new_batter and self.on_batter_found:
                    self.on_batter_found(frame_batter_info)

                # Call progress callback after processing each frame
                if self.on_progress:
                    self.on_progress(frame_count, int(self.total_frames))

        self.batters = BatterInfo([frame for frame in frames if frame.new_batter])
        logger.info(f"{self.batters=}")
        self.batter_count = len(self.batters)
        logger.info(f"{self.batter_count=}")
        return self
