"""Template matching for detecting specific patterns in video frames."""

import logging
from collections import namedtuple
from functools import cached_property
from typing import Literal, NamedTuple, Union

import cv2 as cv
import numpy as np

from .geometry import Point, Size

logger = logging.getLogger(__name__)

MatchConfig = namedtuple("MatchConfig", "image, templ, method")


class MatchTemplateResult(NamedTuple):
    """Results from a template matching operation.

    Attributes:
        is_match: Whether the template was found above threshold.
        score: Confidence score from template matching algorithm.
        top_left_point: Top-left corner coordinates of the match location.
    """

    is_match: bool
    score: float
    top_left_point: Point


class MatchDefault(NamedTuple):
    """Default configuration parameters for a template matching method.

    Attributes:
        threshold: Default threshold value for accepting matches.
        optimal_function: Whether to use "min" or "max" for determining best match.
    """

    threshold: float
    optimal_function: Union[Literal["min"], Literal["max"]]


class MatchTemplateScan:
    """Scan an image for the existence of a template pattern."""

    def __init__(self, image: np.ndarray, template: np.ndarray, method: str):
        """Initialize a template matching scanner.

        Args:
            image: Video frame or image to search (grayscale numpy array).
            template: Template pattern to search for (grayscale numpy array).
            method: OpenCV template matching method name (e.g., "TM_CCOEFF_NORMED").

        Note:
            See https://docs.opencv.org/4.x/df/dfb/group__imgproc__object.html
        """
        self.image = image
        self.template = template
        self.method = method

    @property
    def method_default(self) -> dict[str, MatchDefault]:
        """Get default configuration for all template matching methods.

        Returns:
            Dictionary mapping method names to their default configurations.
        """
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
        """Get OpenCV constant value for the template matching method.

        Returns:
            Integer constant from cv2 module (e.g., cv.TM_CCOEFF_NORMED).
        """
        return getattr(cv, self.method)

    @property
    def cfg(self) -> MatchConfig:
        """Get configuration object for template matching.

        Returns:
            MatchConfig namedtuple with image, template, and method.
        """
        return MatchConfig(
            image=self.image, templ=self.template, method=self.method_attr
        )

    @cached_property
    def match(self) -> cv.matchTemplate:
        """Perform template matching operation.

        Returns:
            Result array from cv.matchTemplate showing match scores.
        """
        return cv.matchTemplate(**self.cfg._asdict())

    @property
    def result(self) -> MatchTemplateResult:
        """Get the final match result with threshold and quadrant checks.

        Returns:
            MatchTemplateResult with match status, score, and location.
        """
        meets_threshold, score, top_left_loc = self.parse_match_result()

        in_quadrant = self.match_quadrant(top_left_loc)

        is_match = meets_threshold and in_quadrant
        logger.debug(f"{is_match=}")

        return MatchTemplateResult(is_match, score, top_left_loc)

    def match_quadrant(self, match_top_left) -> bool:
        """Check if match is located in the bottom-left quadrant of the image.

        Args:
            match_top_left: Top-left corner Point of the match location.

        Returns:
            True if match is in bottom-left quadrant, False otherwise.
        """
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
        """Parse raw template match results based on method type.

        Different template matching methods require min or max interpretation.
        This method applies the correct logic based on the chosen method.

        Returns:
            Tuple of (meets_threshold, score, top_left_location).
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
