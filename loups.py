import logging
from collections import namedtuple
from datetime import timedelta

import cv2 as cv

FrameBatterInfo = namedtuple(
    "FrameBatterInfo", "ms, match_score, is_batter, new_batter, batter_name"
)


class MilliSecond(float):
    def __str__(self):
        return self.yt_format()

    def yt_format(self) -> str:
        td = timedelta(milliseconds=self)

        hours = td / timedelta(hours=1)
        minutes = td / timedelta(minutes=1)
        seconds = td.seconds

        return f"{hours:02.0f}:{minutes:02.0f}:{seconds:02.0f}"


class BatterInfo(list):
    def __str__(self):
        return "\n".join(
            [" ".join([str(frame.ms), frame.batter_name]) for frame in self]
        )


class Loups:
    """Extract the video timestamp when each batter is up"""

    METHOD_DEFAULT = {"TM_CCOEFF_NORMED": {"threshold": 0.43, "optimal_func": "max"}}

    def __init__(
        self,
        scannable,
        template,
        method="TM_CCOEFF_NORMED",
        threshold=None,
        resolution=3,
    ):
        """
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

        self.logger = logging.getLogger(__name__)
        self._scannable = scannable
        self._capture = self.create_capture()
        self._frame_rate = self.get_frame_rate()
        self.template = template
        self._method = method
        self.threshold = self.get_threshold(threshold)
        self._method_optimal_func = self.get_method_optimal_func()
        self.resolution = resolution

    @property
    def method(self):
        return self._method

    @property
    def scannable(self):
        return self._scannable

    @property
    def capture(self):
        return self._capture

    @property
    def frame_rate(self):
        return self._frame_rate

    @property
    def method_optimal_func(self):
        return self._method_optimal_func

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, value):
        self._template = cv.imread(value, cv.IMREAD_GRAYSCALE)

    def get_method_optimal_func(self):
        mof = self.METHOD_DEFAULT.get(self.method).get("optimal_func")
        valid = ["min", "max"]
        assert mof in valid, f"optimal_func must be: min or max.  {mof=} is not valid."
        return mof

    def get_threshold(self, value):
        return (
            value
            if value is not None
            else self.METHOD_DEFAULT.get(self.method).get("threshold")
        )

    def create_capture(self) -> cv.VideoCapture:
        return cv.VideoCapture(self.scannable)

    def get_frame_rate(self) -> float:
        """return frame rate of scannable
        https://docs.opencv.org/4.x/d4/d15/group__videoio__flags__base.html#gaeb8dd9c89c10a5c63c139bf7c4f5704d
        """
        return self.capture.get(5)

    def frame_frequency(self) -> int:
        """Specifies how many frames to skip before processing a new frame"""
        return int(self.frame_rate / self.resolution)

    def timestamp(self):
        """Returns timestamp of video frame in ms"""
        return self.capture.get(0)

    def method_attribute_index(self) -> int:
        return getattr(cv, self.method)

    def is_batter(self, frame) -> tuple[float, bool]:
        """Returns True if a new batter is up"""

        cfg = {
            "image": cv.cvtColor(frame, cv.COLOR_BGR2GRAY),
            "templ": self.template,
            "method": self.method_attribute_index(),
        }
        # self.logger.debug(f"{cfg=}")

        match = cv.matchTemplate(**cfg)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(match)

        match self.method_optimal_func:
            case "max":
                score = max_val
                is_batter_graphic = max_val >= self.threshold
            case "min":
                score = min_val
                is_batter_graphic = min_val <= self.threshold

        return score, is_batter_graphic

    def new_batter(self, res, ms, is_batter, threshold: int = 2000) -> bool:
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
        """Returns the timestamp in ms of the last frame which included a batter"""
        try:
            ts = max(b.ms for b in res if b.is_batter)
        except ValueError:
            ts = None
        return ts

    @staticmethod
    def prev_frame_is_batter(res: list) -> bool:
        try:
            prev_frame_is_batter = res[-1].is_batter
        except IndexError:
            prev_frame_is_batter = False
        return prev_frame_is_batter

    @staticmethod
    def batter_name() -> str:
        return "batter"

    def scan(self):
        """Create a collection of images"""
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


def main():
    TEMPLATE = "data/template2.png"
    TEMPLATE = "data/template_solid.png"
    VIDEO = "data/lightsout_20251012_ruffrydaz12u.mp4"
    VIDEO = "data/emerald1.mp4"
    VIDEO = "data/lbvibe2.mp4"

    logging.basicConfig(level=logging.INFO)
    game = Loups(VIDEO, TEMPLATE).scan()
    print(game.batters)


if __name__ == "__main__":
    main()
