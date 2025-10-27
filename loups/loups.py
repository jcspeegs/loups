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

import cv2 as cv

Point = namedtuple("Point", "x, y")
Size = namedtuple("Size", "height, width")
MatchDefault = namedtuple("MatchDefault", "threshold, optimal_function")
MatchConfig = namedtuple("MatchConfig", "image, templ, method")
FrameBatterInfo = namedtuple(
    "FrameBatterInfo",
    "ms, match_score, is_batter, new_batter, batter_name",
)


# TODO: Restrict to >= 0
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


class BatterInfo(list):
    """A collection of FrameBatterInfo objects."""

    def __str__(self):
        """Display BatterInfo as needed to create YouTube video chapters."""
        return "\n".join(
            [" ".join([str(frame.ms), frame.batter_name]) for frame in self]
        )


class Loups:
    """Extract batter information from Lights Out HB fastpitch videos."""

    logger = logging.getLogger(__name__)
    METHOD_DEFAULT = {
        "TM_CCOEFF_NORMED": MatchDefault(threshold=0.43, optimal_function="max"),
    }

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
        self._method_default = Loups.METHOD_DEFAULT.get(self.method)
        self.threshold = (
            threshold if threshold is not None else self.method_default.threshold
        )
        self._method_optimal_func = self.get_method_optimal_func()
        self.resolution = resolution

    @property
    def method(self):
        """Returns the method used for template matching."""
        return self._method

    @property
    def method_default(self):
        """Returns the defaults for self.method."""
        return self._method_default

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
    def method_optimal_func(self):
        """Returns the function (min/max) to find the optimum match method result."""
        return self._method_optimal_func

    @property
    def template(self):
        """Returns an image as a numpy ndarray."""
        return self._template

    @template.setter
    def template(self, value):
        self._template = cv.imread(value, cv.IMREAD_GRAYSCALE)

    def get_method_optimal_func(self):
        """Get the function used to determine the opimal match template result."""
        mof = self.method_default.optimal_function
        valid = ["min", "max"]
        assert mof in valid, f"optimal_func must be: min or max.  {mof=} is not valid."
        return mof

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

    def method_attribute_index(self) -> int:
        """Get the index used to access a given match template method attribute."""
        return getattr(cv, self.method)

    def is_batter(self, frame) -> tuple[float, bool]:
        """Determine if a frame contains an upcoming batter.

        Returns a tuple of the form (confidence score, boolean)
        """
        cfg = MatchConfig(
            image=cv.cvtColor(frame, cv.COLOR_BGR2GRAY),
            templ=self.template,
            method=self.method_attribute_index(),
        )
        self.logger.debug(f"{cfg=}")

        match = cv.matchTemplate(**cfg._asdict())
        self.logger.debug(f"{match=}")
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(match)

        match self.method_optimal_func:
            case "max":
                score = max_val
                is_batter_graphic = max_val >= self.threshold
                match_top_left = Point(*max_loc)
            case "min":
                score = min_val
                is_batter_graphic = min_val <= self.threshold
                match_top_left = Point(*min_loc)

        in_bottom_left_quadrant = self.match_in_quadrant(match_top_left, cfg)
        self.logger.debug(f"{in_bottom_left_quadrant=}")

        is_batter = is_batter_graphic and in_bottom_left_quadrant
        self.logger.debug(f"{is_batter=}")

        return score, is_batter

    def new_batter(self, res, ms, is_batter, threshold: int = 2000) -> bool:
        """Determine if a frame conatins a new batter."""
        prev_frame_is_batter = self.prev_frame_is_batter(res)
        new_batter_frame = is_batter and not prev_frame_is_batter

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

    def prev_batter_frame_timestamp(self, res) -> int:
        """Get the timestamp in ms of the previous frame which included a batter."""
        try:
            ts = max(b.ms for b in res if b.is_batter)
        except ValueError:
            ts = None
        return ts

    @staticmethod
    def prev_frame_is_batter(res: list) -> bool:
        """Determine if the previous frame contained a batter."""
        try:
            prev_frame_is_batter = res[-1].is_batter
        except IndexError:
            prev_frame_is_batter = False
        return prev_frame_is_batter

    @staticmethod
    def batter_name() -> str:
        """Determine batter name."""
        return "batter"

    @staticmethod
    def match_in_quadrant(match_top_left: Point, match_config: MatchConfig) -> bool:
        """Test if match is in the bottom left quadrant of image."""
        graphic_size = Size(*match_config.templ.shape)
        Loups.logger.debug(f"{graphic_size=}")

        Loups.logger.debug(f"{match_top_left=}")
        match_bottom_left = Point(
            match_top_left.x, match_top_left.y + graphic_size.height
        )
        Loups.logger.debug(f"{match_bottom_left=}")

        image_size = Size(*match_config.image.shape)
        Loups.logger.debug(f"{image_size=}")

        is_match_in_quadrant = (match_bottom_left.x < 0.5 * image_size.width) and (
            match_bottom_left.y > 0.5 * image_size.height
        )
        Loups.logger.debug(f"{is_match_in_quadrant=}")

        return is_match_in_quadrant

    def scan(self):
        """Scan a scannable for a template."""
        frame_count = 0

        frames = []
        while True:
            ret = self.capture.grab()

            if not ret:
                break

            frame_count += 1
            self.logger.debug(f"{frame_count=}")
            frame_frequency = self.frame_frequency()
            keep_frame = frame_count % frame_frequency == 0
            self.logger.debug(f"{keep_frame=}")
            if keep_frame:
                ret, frame = self.capture.retrieve()

                ms = MilliSecond(self.timestamp())
                match_score, is_batter = self.is_batter(frame)
                new_batter = self.new_batter(frames, ms, is_batter)
                new_batter_name = self.batter_name() if new_batter else None

                frame_batter_info = FrameBatterInfo(
                    ms=ms,
                    match_score=match_score,
                    is_batter=is_batter,
                    new_batter=new_batter,
                    batter_name=new_batter_name,
                )
                self.logger.debug(f"{frame_batter_info=}")
                frames.append(frame_batter_info)

        self.batters = BatterInfo([frame for frame in frames if frame.new_batter])
        self.logger.info(f"{self.batters=}")
        self.batter_count = len(self.batters)
        self.logger.info(f"{self.batter_count=}")
        return self
