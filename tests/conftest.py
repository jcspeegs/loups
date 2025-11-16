"""Configure pytest for loups."""

from unittest.mock import Mock, patch

import cv2 as cv
import numpy as np
import pytest

import loups.loups as loups

# ============================================================================
# Existing Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def list_frame_batter_info():
    """Provide a BatterInfo fixture."""
    list_frame_batter_info = [
        loups.FrameBatterInfo(
            ms=loups.MilliSecond(ms),
            match_score=0.85,
            is_batter=True,
            new_batter=True,
            batter_name=f"batter{i}",
        )
        for i, ms in enumerate(range(2000, 400_000, 30_000))
    ]
    yield list_frame_batter_info


# ============================================================================
# Video/Frame Mocking Fixtures
# ============================================================================


@pytest.fixture
def mock_video_capture_30fps():
    """Mock cv2.VideoCapture with 30 fps.

    Returns a context manager that patches cv2.VideoCapture
    to return a mock object configured for 30 fps video.

    Usage:
        def test_something(mock_video_capture_30fps):
            with mock_video_capture_30fps:
                # VideoCapture is now mocked
                pass
    """
    with patch("cv2.VideoCapture") as mock_vc:
        mock_capture = Mock()
        mock_capture.get.return_value = 30.0
        mock_vc.return_value = mock_capture
        yield mock_capture


@pytest.fixture
def mock_video_capture():
    """Create a parameterizable VideoCapture mock factory.

    Returns a function that creates a mock VideoCapture with custom fps.

    Usage:
        def test_something(mock_video_capture):
            mock_vc = mock_video_capture(fps=60.0)
            with patch("cv2.VideoCapture", return_value=mock_vc):
                # Use the mock
                pass
    """

    def _make_mock(fps=30.0):
        mock_capture = Mock()
        mock_capture.get.return_value = fps
        return mock_capture

    return _make_mock


@pytest.fixture
def mock_imread():
    """Mock cv2.imread to return a standard test image.

    Returns a context manager that patches cv2.imread
    to return a 100x100x3 black image.

    Usage:
        def test_something(mock_imread):
            with mock_imread:
                # imread is now mocked
                pass
    """
    with patch("cv2.imread") as mock:
        mock.return_value = np.zeros((100, 100, 3), dtype=np.uint8)
        yield mock


# ============================================================================
# Template/Image Fixtures
# ============================================================================


@pytest.fixture
def mock_template_image(tmp_path):
    """Create a standard 100x100x3 test template image file.

    Creates a black template image and saves it to a temporary file.

    Args:
        tmp_path: pytest's temporary directory fixture

    Returns:
        Path: Path to the created template image file

    Usage:
        def test_something(mock_template_image):
            template_path = mock_template_image
            # Use the template file
    """
    template_path = tmp_path / "template.png"
    template_img = np.zeros((100, 100, 3), dtype=np.uint8)
    cv.imwrite(str(template_path), template_img)
    return template_path


@pytest.fixture
def black_frame():
    """Create a standard black 100x100x3 frame as numpy array.

    Returns:
        np.ndarray: Black image array of shape (100, 100, 3)

    Usage:
        def test_something(black_frame):
            assert black_frame.shape == (100, 100, 3)
    """
    return np.zeros((100, 100, 3), dtype=np.uint8)


@pytest.fixture
def white_frame():
    """Create a standard white 100x100x3 frame as numpy array.

    Returns:
        np.ndarray: White image array of shape (100, 100, 3)

    Usage:
        def test_something(white_frame):
            assert np.all(white_frame == 255)
    """
    return np.ones((100, 100, 3), dtype=np.uint8) * 255


# ============================================================================
# Test Data Fixtures
# ============================================================================


@pytest.fixture
def standard_fps():
    """Return standard test FPS value (30.0).

    Returns:
        float: 30.0 frames per second

    Usage:
        def test_something(standard_fps):
            assert standard_fps == 30.0
    """
    return 30.0


@pytest.fixture
def standard_resolution():
    """Return standard test resolution value (3 frames per second).

    Returns:
        int: 3 frames per second sampling resolution

    Usage:
        def test_something(standard_resolution):
            assert standard_resolution == 3
    """
    return 3


@pytest.fixture
def sample_ocr_results():
    """Return common OCR test data structure.

    Returns a list of OCR results in the format:
    [((x1, y1, x2, y2), "text", confidence), ...]

    Returns:
        list: Sample OCR results with name and jersey number

    Usage:
        def test_something(sample_ocr_results):
            name = extract_name(sample_ocr_results)
            assert name == "Jane Doe #12"
    """
    return [
        ((0, 0, 100, 20), "Jane Doe", 0.95),
        ((100, 0, 120, 20), "#12", 0.88),
    ]
