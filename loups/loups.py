"""
Scan a Lights Out HB fastpitch game video and extract information.

Game information currently extracted:
  * Timestamps of each Lights Out HB batter
  * Total number of Lights Out HB batters
  * ...
"""

import logging
from collections import namedtuple
from datetime import timedelta
from functools import cached_property
from typing import Literal, NamedTuple, Union

import cv2 as cv
import easyocr
import numpy as np

logger = logging.getLogger(__name__)

Point = namedtuple("Point", "x, y")
Size = namedtuple("Size", "height, width")
MatchConfig = namedtuple("MatchConfig", "image, templ, method")


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
        seconds = td.seconds % 60

        return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"


class FrameBatterInfo(NamedTuple):
    """Holds batter information for a frame of a video."""

    ms: MilliSecond
    match_score: float
    is_batter: bool
    new_batter: bool
    batter_name: str


class MatchDefault(NamedTuple):
    """Holds default match method configuration parameters."""

    threshold: float
    optimal_function: Union[Literal["min"], Literal["max"]]


class MatchTemplateResult(NamedTuple):
    """Hold the results of matchTemplate scans."""

    is_match: bool
    score: float
    top_left_point: Point


class MatchTemplateScan:
    """Scan an image for the existence of a template."""

    def __init__(self, image: np.ndarray, template: np.ndarray, method: str):
        """Initialize a new instance of MatchTemplateScan.

        Parameters
            image: A video frame or image after being read by cv.VideoCapture
            template: An image to search for in self.image
            method: The match method to use in your search
                    (https://docs.opencv.org/4.x/df/dfb/group__imgproc__object.html#ga3a7850640f1fe1f58fe91a2d7583695d)
        """
        self.image = image
        self.template = template
        self.method = method

    @property
    def method_default(self) -> dict[str, MatchDefault]:
        """Match template method default config options."""
        return {
            "TM_SQDIFF": MatchDefault(threshold=None, optimal_function="min"),
            "TM_SQDIFF_NORMED": MatchDefault(threshold=None, optimal_function="min"),
            "TM_CCORR": MatchDefault(threshold=None, optimal_function="max"),
            "TM_CCORR_NORMED": MatchDefault(threshold=None, optimal_function="max"),
            "TM_CCOEFF": MatchDefault(threshold=None, optimal_function="max"),
            "TM_CCOEFF_NORMED": MatchDefault(threshold=0.43, optimal_function="max"),
        }

    @property
    def method_attr(self) -> int:
        """Convert a match template method name to its index integer."""
        return getattr(cv, self.method)

    @property
    def cfg(self) -> MatchConfig:
        """Return a match template config object."""
        return MatchConfig(
            image=self.image, templ=self.template, method=self.method_attr
        )

    @cached_property
    def match(self) -> cv.matchTemplate:
        """Scan an image for a template image."""
        return cv.matchTemplate(**self.cfg._asdict())

    @property
    def result(self) -> MatchTemplateResult:
        """Return the relevant matchTemplate score and location."""
        meets_threshold, score, top_left_loc = self.parse_match_result()

        in_quadrant = self.match_quadrant(top_left_loc)

        is_match = meets_threshold and in_quadrant
        logger.debug(f"{is_match=}")

        return MatchTemplateResult(is_match, score, top_left_loc)

    def match_quadrant(self, match_top_left) -> bool:
        """Determine if a match is found in the bottom left quadrant."""
        template_size = Size(*self.template.shape)
        logger.debug(f"{template_size=}")

        match_bottom_left = Point(
            match_top_left.x, match_top_left.y + template_size.height
        )
        logger.debug(f"{match_bottom_left=}")

        image_size = Size(*self.image.shape)
        logger.debug(f"{image_size=}")

        is_bottom_left_quadrant = (match_bottom_left.x < 0.5 * image_size.width) and (
            match_bottom_left.y > 0.5 * image_size.height
        )
        logger.debug(f"{is_bottom_left_quadrant=}")

        return is_bottom_left_quadrant

    def parse_match_result(self) -> tuple[bool, float, Point]:
        """Interpret match result.

        Depending on the matchTemplate method used, we either want to work with the min
        or max return score and return location.
        """
        default = self.method_default.get(self.method)
        logger.debug(f"{default=}")
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(self.match)

        match default.optimal_function:
            case "max":
                score = max_val
                is_match = max_val >= default.threshold
                top_left_loc = Point(*max_loc)
            case "min":
                score = min_val
                is_match = min_val <= default.threshold
                top_left_loc = Point(*min_loc)

        return is_match, score, top_left_loc


class BatterInfo(list):
    """A collection of FrameBatterInfo objects."""

    def __str__(self):
        """Display BatterInfo as needed to create YouTube video chapters."""
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

    def batter_name(self, match_top_left) -> str:
        """Determine batter name."""
        logger.debug(f"{match_top_left=}")
        result = Loups.reader.readtext(self.frame)
        logger.debug(f"{result=}")
        return "batter"

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
