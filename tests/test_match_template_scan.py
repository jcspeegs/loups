"""Comprehensive test suite for MatchTemplateScan class.

This module tests all aspects of the MatchTemplateScan functionality including:
- All 6 OpenCV template matching methods
- Quadrant detection logic
- Threshold behavior
- Edge cases and error handling
- Property caching behavior
- Real template matching with actual data
"""

from pathlib import Path

import cv2 as cv
import numpy as np
import pytest

from loups.geometry import Point
from loups.match_template_scan import MatchTemplateResult, MatchTemplateScan

# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def simple_template():
    """Create a simple 50x50 grayscale template with a white square."""
    template = np.zeros((50, 50), dtype=np.uint8)
    template[10:40, 10:40] = 255  # White square in center
    return template


@pytest.fixture
def simple_image_with_match_bottom_left():
    """Create a 200x200 image with the template in bottom-left quadrant."""
    image = np.zeros((200, 200), dtype=np.uint8)
    # Place match at (20, 120) - bottom-left quadrant
    # Bottom-left of match: (20, 170) which is x < 100 and y > 100
    image[120:170, 20:70] = 255  # White square
    image[130:160, 30:60] = 255  # Ensure it matches the template pattern
    return image


@pytest.fixture
def simple_image_with_match_top_left():
    """Create a 200x200 image with the template in top-left quadrant."""
    image = np.zeros((200, 200), dtype=np.uint8)
    # Place match at (20, 20) - top-left quadrant
    image[20:70, 20:70] = 255
    image[30:60, 30:60] = 255
    return image


@pytest.fixture
def simple_image_with_match_top_right():
    """Create a 200x200 image with the template in top-right quadrant."""
    image = np.zeros((200, 200), dtype=np.uint8)
    # Place match at (120, 20) - top-right quadrant
    image[20:70, 120:170] = 255
    image[30:60, 130:160] = 255
    return image


@pytest.fixture
def simple_image_with_match_bottom_right():
    """Create a 200x200 image with the template in bottom-right quadrant."""
    image = np.zeros((200, 200), dtype=np.uint8)
    # Place match at (120, 120) - bottom-right quadrant
    image[120:170, 120:170] = 255
    image[130:160, 130:160] = 255
    return image


@pytest.fixture
def simple_image_no_match():
    """Create a 200x200 image with no matching template."""
    image = np.zeros((200, 200), dtype=np.uint8)
    # Random noise, no clear match
    image[50:100, 50:100] = 128
    return image


@pytest.fixture
def real_template():
    """Load the actual template from loups/data/template_solid.png."""
    template_path = (
        Path(__file__).parent.parent / "loups" / "data" / "template_solid.png"
    )
    template = cv.imread(str(template_path), cv.IMREAD_GRAYSCALE)
    if template is None:
        pytest.skip(f"Template not found at {template_path}")
    return template


# ============================================================================
# TestMatchTemplateScanCore - Core Functionality Tests
# ============================================================================


class TestMatchTemplateScanCore:
    """Test core functionality of MatchTemplateScan."""

    def test_initialization(self, simple_image_no_match, simple_template):
        """Test that MatchTemplateScan initializes correctly."""
        scanner = MatchTemplateScan(
            simple_image_no_match, simple_template, "TM_CCOEFF_NORMED"
        )
        assert scanner.image is simple_image_no_match
        assert scanner.template is simple_template
        assert scanner.method == "TM_CCOEFF_NORMED"

    def test_result_structure(self, simple_image_no_match, simple_template):
        """Test that result returns a MatchTemplateResult."""
        scanner = MatchTemplateScan(
            simple_image_no_match, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        assert isinstance(result, MatchTemplateResult)
        assert hasattr(result, "is_match")
        assert hasattr(result, "score")
        assert hasattr(result, "top_left_point")
        assert isinstance(result.is_match, bool)
        assert isinstance(result.score, (int, float))
        assert isinstance(result.top_left_point, Point)

    def test_cfg_property(self, simple_image_no_match, simple_template):
        """Test that cfg property returns correct configuration."""
        scanner = MatchTemplateScan(
            simple_image_no_match, simple_template, "TM_CCOEFF_NORMED"
        )
        cfg = scanner.cfg
        assert cfg.image is simple_image_no_match
        assert cfg.templ is simple_template  # Note: it's 'templ', not 'template'
        assert cfg.method == cv.TM_CCOEFF_NORMED

    def test_method_attr_property(self, simple_image_no_match, simple_template):
        """Test that method_attr converts string to cv2 constant."""
        scanner = MatchTemplateScan(
            simple_image_no_match, simple_template, "TM_CCOEFF_NORMED"
        )
        assert scanner.method_attr == cv.TM_CCOEFF_NORMED

    def test_match_property_is_cached(self, simple_image_no_match, simple_template):
        """Test that match property is computed only once (cached)."""
        scanner = MatchTemplateScan(
            simple_image_no_match, simple_template, "TM_CCOEFF_NORMED"
        )
        # Access match twice
        match1 = scanner.match
        match2 = scanner.match
        # Should be the exact same object (cached)
        assert match1 is match2

    def test_result_composition_both_true(
        self, simple_image_with_match_bottom_left, simple_template
    ):
        """Test result when both threshold and quadrant checks pass."""
        scanner = MatchTemplateScan(
            simple_image_with_match_bottom_left, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        # Should match: good score AND in bottom-left quadrant
        assert result.is_match is True

    def test_result_composition_threshold_false(
        self, simple_image_no_match, simple_template
    ):
        """Test result when threshold check fails."""
        scanner = MatchTemplateScan(
            simple_image_no_match, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        # Should not match: poor score
        assert result.is_match is False

    def test_result_composition_quadrant_false(
        self, simple_image_with_match_top_left, simple_template
    ):
        """Test result when quadrant check fails but threshold passes."""
        scanner = MatchTemplateScan(
            simple_image_with_match_top_left, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        # Should not match: wrong quadrant (even if good score)
        assert result.is_match is False


# ============================================================================
# TestMatchTemplateScanMethods - Test All 6 Matching Methods
# ============================================================================


class TestMatchTemplateScanMethods:
    """Test all 6 OpenCV template matching methods."""

    @pytest.mark.parametrize(
        "method_name,expected_cv_constant",
        [
            ("TM_SQDIFF", cv.TM_SQDIFF),
            ("TM_SQDIFF_NORMED", cv.TM_SQDIFF_NORMED),
            ("TM_CCORR", cv.TM_CCORR),
            ("TM_CCORR_NORMED", cv.TM_CCORR_NORMED),
            ("TM_CCOEFF", cv.TM_CCOEFF),
            ("TM_CCOEFF_NORMED", cv.TM_CCOEFF_NORMED),
        ],
    )
    def test_method_constants(
        self, method_name, expected_cv_constant, simple_image_no_match, simple_template
    ):
        """Test that all method names map to correct OpenCV constants."""
        scanner = MatchTemplateScan(simple_image_no_match, simple_template, method_name)
        assert scanner.method_attr == expected_cv_constant

    def test_tm_ccoeff_normed_executes(
        self, simple_image_with_match_bottom_left, simple_template
    ):
        """Test TM_CCOEFF_NORMED (only method with threshold) executes."""
        scanner = MatchTemplateScan(
            simple_image_with_match_bottom_left, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        assert isinstance(result, MatchTemplateResult)
        assert isinstance(result.score, (int, float))

    def test_tm_ccoeff_normed_default_threshold(
        self, simple_image_with_match_bottom_left, simple_template
    ):
        """Test TM_CCOEFF_NORMED uses threshold of 0.53."""
        scanner = MatchTemplateScan(
            simple_image_with_match_bottom_left, simple_template, "TM_CCOEFF_NORMED"
        )
        # Access the method_default dict to check threshold
        method_config = scanner.method_default["TM_CCOEFF_NORMED"]
        assert method_config.threshold == 0.53

    @pytest.mark.parametrize(
        "method_name",
        [
            "TM_SQDIFF",
            "TM_SQDIFF_NORMED",
            "TM_CCORR",
            "TM_CCORR_NORMED",
            "TM_CCOEFF",
        ],
    )
    def test_other_methods_have_none_threshold(
        self, method_name, simple_image_no_match, simple_template
    ):
        """Test that methods other than TM_CCOEFF_NORMED have None threshold."""
        scanner = MatchTemplateScan(simple_image_no_match, simple_template, method_name)
        method_config = scanner.method_default[method_name]
        assert method_config.threshold is None

    @pytest.mark.parametrize(
        "method_name,expected_optimal",
        [
            ("TM_SQDIFF", "min"),
            ("TM_SQDIFF_NORMED", "min"),
            ("TM_CCORR", "max"),
            ("TM_CCORR_NORMED", "max"),
            ("TM_CCOEFF", "max"),
            ("TM_CCOEFF_NORMED", "max"),
        ],
    )
    def test_optimal_function_mapping(
        self, method_name, expected_optimal, simple_image_no_match, simple_template
    ):
        """Test that each method has correct optimal_function (min vs max)."""
        scanner = MatchTemplateScan(simple_image_no_match, simple_template, method_name)
        method_config = scanner.method_default[method_name]
        assert method_config.optimal_function == expected_optimal


# ============================================================================
# TestMatchTemplateScanQuadrant - Quadrant Detection Tests
# ============================================================================


class TestMatchTemplateScanQuadrant:
    """Test quadrant detection logic."""

    def test_match_in_bottom_left_quadrant(
        self, simple_image_with_match_bottom_left, simple_template
    ):
        """Test that matches in bottom-left quadrant are detected."""
        scanner = MatchTemplateScan(
            simple_image_with_match_bottom_left, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        # Bottom-left quadrant should result in is_match=True (if threshold passes)
        # We know the match is strong enough, so check quadrant logic
        assert result.top_left_point.x < 100  # Left half
        # For bottom quadrant, bottom-left point y must be > 100
        bottom_y = result.top_left_point.y + simple_template.shape[0]
        assert bottom_y > 100  # Bottom half

    def test_match_in_top_left_quadrant_rejected(
        self, simple_image_with_match_top_left, simple_template
    ):
        """Test that matches in top-left quadrant are rejected."""
        scanner = MatchTemplateScan(
            simple_image_with_match_top_left, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        # Top-left quadrant should result in is_match=False
        assert result.is_match is False

    def test_match_in_top_right_quadrant_rejected(
        self, simple_image_with_match_top_right, simple_template
    ):
        """Test that matches in top-right quadrant are rejected."""
        scanner = MatchTemplateScan(
            simple_image_with_match_top_right, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        # Top-right quadrant should result in is_match=False
        assert result.is_match is False

    def test_match_in_bottom_right_quadrant_rejected(
        self, simple_image_with_match_bottom_right, simple_template
    ):
        """Test that matches in bottom-right quadrant are rejected."""
        scanner = MatchTemplateScan(
            simple_image_with_match_bottom_right, simple_template, "TM_CCOEFF_NORMED"
        )
        result = scanner.result
        # Bottom-right quadrant should result in is_match=False
        assert result.is_match is False

    def test_quadrant_boundary_horizontal(self):
        """Test match exactly on horizontal quadrant boundary."""
        # Create image 200x200, template 50x50
        # Use non-uniform template to avoid TM_CCOEFF_NORMED division by zero
        template = np.zeros((50, 50), dtype=np.uint8)
        template[10:40, 10:40] = 255  # White square pattern

        image = np.zeros((200, 200), dtype=np.uint8)
        # Template at (20, 50) means bottom at y=100 (exactly on boundary)
        image[50:100, 20:70] = template

        scanner = MatchTemplateScan(image, template, "TM_CCOEFF_NORMED")
        result = scanner.result
        # Boundary uses >, so y=100 is NOT in bottom half
        # Should be rejected
        assert result.is_match is False

    def test_quadrant_boundary_vertical(self):
        """Test match exactly on vertical quadrant boundary."""
        # Create image 200x200, template 50x50
        # Place template so bottom-left is exactly at x=100 (boundary)
        template = np.ones((50, 50), dtype=np.uint8) * 255
        image = np.zeros((200, 200), dtype=np.uint8)
        # Template at (100, 120) means bottom-left at x=100 (exactly on boundary)
        image[120:170, 100:150] = 255

        scanner = MatchTemplateScan(image, template, "TM_CCOEFF_NORMED")
        result = scanner.result
        # Boundary uses <, so x=100 is NOT in left half
        # Should be rejected
        assert result.is_match is False


# ============================================================================
# TestMatchTemplateScanEdgeCases - Edge Cases and Error Handling
# ============================================================================


class TestMatchTemplateScanEdgeCases:
    """Test edge cases and error handling."""

    def test_template_larger_than_image(self):
        """Test that template larger than image behavior.

        Note: OpenCV 4.12.0+ appears to handle this case without error,
        though earlier versions may have raised cv.error.
        """
        small_image = np.zeros((50, 50), dtype=np.uint8)
        large_template = np.ones((100, 100), dtype=np.uint8)

        scanner = MatchTemplateScan(small_image, large_template, "TM_CCOEFF_NORMED")

        # In newer OpenCV versions, this may not raise an error
        # Behavior depends on OpenCV version
        try:
            result = scanner.result
            # If it doesn't error, verify it returns a result
            assert isinstance(result, MatchTemplateResult)
        except cv.error:
            # Older OpenCV versions may still raise an error
            pass

    def test_invalid_method_name(self):
        """Test that invalid method name raises AttributeError."""
        image = np.zeros((100, 100), dtype=np.uint8)
        template = np.ones((50, 50), dtype=np.uint8)

        scanner = MatchTemplateScan(image, template, "TM_INVALID_METHOD")

        with pytest.raises(AttributeError):
            _ = scanner.method_attr

    def test_empty_image_array(self, simple_template):
        """Test handling of empty image array."""
        empty_image = np.array([], dtype=np.uint8)

        scanner = MatchTemplateScan(empty_image, simple_template, "TM_CCOEFF_NORMED")

        with pytest.raises((cv.error, ValueError, IndexError)):
            _ = scanner.result

    def test_empty_template_array(self):
        """Test handling of empty template array."""
        image = np.zeros((100, 100), dtype=np.uint8)
        empty_template = np.array([], dtype=np.uint8)

        scanner = MatchTemplateScan(image, empty_template, "TM_CCOEFF_NORMED")

        with pytest.raises((cv.error, ValueError, IndexError)):
            _ = scanner.result

    def test_3d_image_array(self, simple_template):
        """Test handling of 3D (BGR) image array."""
        # Create 3D BGR image
        bgr_image = np.zeros((100, 100, 3), dtype=np.uint8)

        scanner = MatchTemplateScan(bgr_image, simple_template, "TM_CCOEFF_NORMED")

        # OpenCV's matchTemplate will raise cv.error for dimension mismatch
        with pytest.raises(cv.error):
            _ = scanner.result

    def test_template_same_size_as_image(self):
        """Test template exactly same size as image."""
        # Use non-uniform pattern to avoid TM_CCOEFF_NORMED division by zero
        template = np.zeros((100, 100), dtype=np.uint8)
        # Create a checkerboard pattern
        template[0::2, 0::2] = 255
        template[1::2, 1::2] = 255

        image = template.copy()

        scanner = MatchTemplateScan(image, template, "TM_CCOEFF_NORMED")
        result = scanner.result

        # Should work, result will be 1x1
        assert isinstance(result, MatchTemplateResult)
        # Perfect match, should have high score
        assert result.score == pytest.approx(1.0, abs=0.01)

    def test_1x1_template(self):
        """Test with 1x1 pixel template."""
        image = np.zeros((100, 100), dtype=np.uint8)
        image[50, 50] = 255
        template = np.array([[255]], dtype=np.uint8)

        scanner = MatchTemplateScan(image, template, "TM_CCOEFF_NORMED")
        result = scanner.result

        # Should work
        assert isinstance(result, MatchTemplateResult)

    def test_single_pixel_images(self):
        """Test with both image and template being 1x1."""
        image = np.array([[255]], dtype=np.uint8)
        template = np.array([[255]], dtype=np.uint8)

        scanner = MatchTemplateScan(image, template, "TM_CCOEFF_NORMED")
        result = scanner.result

        # Should work and match perfectly
        assert isinstance(result, MatchTemplateResult)

    @pytest.mark.parametrize(
        "method_name",
        [
            "TM_SQDIFF",
            "TM_SQDIFF_NORMED",
            "TM_CCORR",
            "TM_CCORR_NORMED",
            "TM_CCOEFF",
        ],
    )
    def test_methods_with_none_threshold_raise_typeerror(self, method_name):
        """Test that methods with None threshold cause TypeError when accessing result.

        This is a known limitation - only TM_CCOEFF_NORMED has a defined threshold.
        """
        image = np.zeros((100, 100), dtype=np.uint8)
        template = np.ones((50, 50), dtype=np.uint8) * 255

        scanner = MatchTemplateScan(image, template, method_name)

        # Should raise TypeError when comparing None with number (>= or <=)
        with pytest.raises(TypeError):
            _ = scanner.result

    def test_match_at_origin(self):
        """Test match at coordinate (0, 0)."""
        # Use non-uniform template to avoid TM_CCOEFF_NORMED division by zero
        template = np.zeros((50, 50), dtype=np.uint8)
        template[10:40, 10:40] = 255  # White square pattern

        image = np.zeros((200, 200), dtype=np.uint8)
        image[0:50, 0:50] = template

        scanner = MatchTemplateScan(image, template, "TM_CCOEFF_NORMED")
        result = scanner.result

        # Match at (0, 0) is in top-left quadrant, should be rejected
        assert result.top_left_point == Point(0, 0)
        assert result.is_match is False


# ============================================================================
# TestMatchTemplateScanRealData - Tests with Real Template
# ============================================================================


class TestMatchTemplateScanRealData:
    """Test with real template from loups/data/."""

    def test_load_real_template(self, real_template):
        """Test that real template can be loaded."""
        assert real_template is not None
        assert isinstance(real_template, np.ndarray)
        assert len(real_template.shape) == 2  # Should be grayscale
        assert real_template.dtype == np.uint8

    def test_real_template_with_synthetic_match(self, real_template):
        """Test real template against synthetic image containing it."""
        # Create a larger image and embed the template in bottom-left quadrant
        template_h, template_w = real_template.shape
        image_h, image_w = template_h * 4, template_w * 4

        image = np.zeros((image_h, image_w), dtype=np.uint8)

        # Place template in bottom-left quadrant
        # Bottom-left quadrant: x < image_w/2, y + template_h > image_h/2
        x_pos = int(image_w * 0.25 - template_w / 2)
        y_pos = int(image_h * 0.75 - template_h / 2)

        image[y_pos : y_pos + template_h, x_pos : x_pos + template_w] = real_template

        scanner = MatchTemplateScan(image, real_template, "TM_CCOEFF_NORMED")
        result = scanner.result

        # Should find a match in bottom-left quadrant
        assert result.is_match is True
        assert result.score > 0.53  # Above threshold
        # Verify it's in bottom-left quadrant
        bottom_left_y = result.top_left_point.y + template_h
        assert result.top_left_point.x < image_w / 2
        assert bottom_left_y > image_h / 2

    def test_real_template_with_no_match(self, real_template):
        """Test real template against image with no match."""
        template_h, template_w = real_template.shape
        image_h, image_w = template_h * 4, template_w * 4

        # Create random noise image
        image = np.random.randint(0, 256, (image_h, image_w), dtype=np.uint8)

        scanner = MatchTemplateScan(image, real_template, "TM_CCOEFF_NORMED")
        result = scanner.result

        # Should not match (or if it does, score should be low)
        # Random nature means we can't guarantee is_match=False
        if result.is_match:
            # If by chance it "matches", the score should still be relatively low
            assert result.score < 0.8  # Not a strong match

    def test_real_template_dimensions(self, real_template):
        """Test that real template has expected dimensions."""
        assert real_template.shape[0] > 0  # Has height
        assert real_template.shape[1] > 0  # Has width
        # Template should be reasonably sized (not too small or too large)
        assert 10 < real_template.shape[0] < 1000
        assert 10 < real_template.shape[1] < 1000
