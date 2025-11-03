"""Scan an image for existance of a template image."""

import logging
from collections import namedtuple
from functools import cached_property
from typing import Literal, NamedTuple, Union

import cv2 as cv
import numpy as np

from .common_components import Point, Size

logger = logging.getLogger(__name__)

MatchConfig = namedtuple("MatchConfig", "image, templ, method")


class MatchTemplateResult(NamedTuple):
    """Hold the results of matchTemplate scans."""

    is_match: bool
    score: float
    top_left_point: Point


class MatchDefault(NamedTuple):
    """Holds default match method configuration parameters."""

    threshold: float
    optimal_function: Union[Literal["min"], Literal["max"]]


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
            "TM_CCOEFF_NORMED": MatchDefault(threshold=0.53, optimal_function="max"),
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
