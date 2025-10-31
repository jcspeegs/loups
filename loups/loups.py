"""
Scan a Lights Out HB fastpitch game video and extract information.

Game information currently extracted:
  * Timestamps of each Lights Out HB batter
  * Total number of Lights Out HB batters
  * ...
"""

import logging
from datetime import timedelta
from typing import NamedTuple

import cv2 as cv
import easyocr

from .common_components import Point, Size
from .match_template_scan import MatchTemplateResult, MatchTemplateScan

logger = logging.getLogger(__name__)


class MilliSecond(float):
    """Provide a custom millisecond formatter to define YouTube chapters."""

    def __new__(cls, value):
        """Restrict MilliSecond objects to non-negative numbers."""
        if value < 0:
            raise ValueError(
                f"MilliSecond cannot be {value}, " "it must be a non-negative number."
            )
        return super().__new__(cls, value)

    def __str__(self):
        """Override the Float.__str__ to follow YouTube chapter formatting."""
        return self.yt_format()

    def yt_format(self) -> str:
        """Format milliseconds as hh:mm:ss as used in YouTube chapter markers."""
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
    """Holds batter information for a frame of a video."""

    ms: MilliSecond
    match_score: float
    is_batter: bool
    new_batter: bool
    batter_name: str


class BatterInfo(list[FrameBatterInfo]):
    """A collection of FrameBatterInfo objects."""

    def __str__(self):
        """Display BatterInfo."""
        return self.display()

    def display(self) -> str:
        """Display BatterInfo as needed to create YouTube video chapters.

        The first chapter must begin with timestamp 00:00 and chapters must be at least
        10s.  If the first batter is up within the first 10s of the video then move the
        timestamp back to 00:00.
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

    reader = easyocr.Reader(["en"])

    def __init__(
        self,
        scannable,
        template,
        method="TM_CCOEFF_NORMED",
        threshold=None,
        resolution=3,
    ):
        """Loups object constructor.

        Parameters
            template: image used to identify a new batter
            video: video file to parse.  Optional if testing a single image
            method: type of template matching operation (TM_SQDIFF, TM_SQDIFF_NORMED,
            TM_CCORR, TM_CCORR_NORMED, TM_CCOEFF, TM_CCOEFF_NORMED)
            threshold: threshold used to accept a match (differs by method)
            resolution: number of frames to analyze per second

        Examples:
            game = Loups(video) # Initialize game
            print(game) # Print timestamps of at-bats in game
            game[14] # At-bat information for the 15th frame of video
            game.n # Number of batters in game
        """
        self._scannable = scannable
        self._capture = self.create_capture()
        self._frame_rate = self.get_frame_rate()
        self.template = template
        self._method = method
        self.resolution = resolution
        self.search_quadrant = "bottomleft"

    @property
    def method(self):
        """Returns the method used for template matching."""
        return self._method

    @property
    def scannable(self):
        """Returns the file to be scanned."""
        return self._scannable

    @property
    def capture(self):
        """Returns cv.VideoCapture of scannable."""
        return self._capture

    @property
    def frame_rate(self):
        """Returns the frame_rate of scannable."""
        return self._frame_rate

    @property
    def template(self):
        """Returns an image as a numpy ndarray."""
        return self._template

    @template.setter
    def template(self, value):
        self._template = cv.imread(value, cv.IMREAD_GRAYSCALE)

    def create_capture(self) -> cv.VideoCapture:
        """Return the cv.VideoCapture of self.scannable."""
        return cv.VideoCapture(self.scannable)

    def get_frame_rate(self) -> float:
        """Return frame rate of scannable.

        https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
        """
        return self.capture.get(5)

    def frame_frequency(self) -> int:
        """Get the number of frames to skip before processing a new frame."""
        return int(self.frame_rate / self.resolution)

    def timestamp(self):
        """Get the timestamp of video frame in ms."""
        return self.capture.get(0)

    def match_template_scan(self) -> MatchTemplateResult:
        """Search for self.template in an image."""
        scan = MatchTemplateScan(
            image=cv.cvtColor(self.frame, cv.COLOR_BGR2GRAY),
            template=self.template,
            method=self.method,
        )
        return scan

    def new_batter(self, res, ms, threshold: int = 2000) -> bool:
        """Determine if a frame conatins a new batter.

        threshold is the time in ms that can elapse without triggering a new batter
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

    def prev_batter_frame_timestamp(self, frames) -> int:
        """Get the timestamp in ms of the previous frame which included a batter."""
        try:
            ts = max(frame.ms for frame in frames if frame.is_batter)
        except ValueError:
            ts = None
        return ts

    @staticmethod
    def prev_frame_is_not_batter(res: list) -> bool:
        """Determine if the previous frame contained a batter."""
        try:
            prev_frame_is_batter = res[-1].is_batter
        except IndexError:
            prev_frame_is_batter = False
        return not prev_frame_is_batter

    def batter_name(self, match_top_left: Point, threshold: float = 0.2) -> str:
        """Determine batter name."""
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

        ocr = Loups.reader.readtext(image_to_scan)
        logger.debug(f"{ocr=}")
        text = [text for location, text, score in ocr if score > threshold]
        logger.debug(f"{text=}")
        return " ".join(text)

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

    def scan(self):
        """Scan a scannable for a template."""
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
                logger.debug(f"{frame_batter_info=}")
                frames.append(frame_batter_info)

        self.batters = BatterInfo([frame for frame in frames if frame.new_batter])
        logger.info(f"{self.batters=}")
        self.batter_count = len(self.batters)
        logger.info(f"{self.batter_count=}")
        return self
