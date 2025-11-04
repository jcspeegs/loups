"""Tests for thumbnail_extractor module."""

from pathlib import Path
from unittest.mock import Mock, patch

import cv2 as cv
import numpy as np
import pytest

from loups.thumbnail_extractor import (
    ThumbnailExtractor,
    ThumbnailResult,
    calculate_ssim,
    extract_thumbnail,
    generate_default_output_path,
    get_default_thumbnail_template,
    load_template,
)


class TestThumbnailExtractor:
    """Test ThumbnailExtractor class."""

    def test_init(self, tmp_path):
        """Test ThumbnailExtractor initialization."""
        # Create test video and template
        video_path = tmp_path / "test.mp4"
        template_path = tmp_path / "template.png"

        # Create dummy template image
        template_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv.imwrite(str(template_path), template_img)

        # Mock VideoCapture
        with patch("cv2.VideoCapture") as mock_vc:
            mock_capture = Mock()
            mock_capture.get.return_value = 30.0  # 30 fps
            mock_vc.return_value = mock_capture

            extractor = ThumbnailExtractor(
                video_path=video_path,
                template_path=template_path,
                resolution=3,
                scan_duration=120,
                threshold=0.8,
            )

            assert extractor.video_path == video_path
            assert extractor.resolution == 3
            assert extractor.scan_duration == 120
            assert extractor.threshold == 0.8
            assert extractor.frame_rate == 30.0

    def test_frame_frequency(self, tmp_path):
        """Test frame_frequency method."""
        video_path = tmp_path / "test.mp4"
        template_path = tmp_path / "template.png"

        # Create dummy template
        template_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv.imwrite(str(template_path), template_img)

        with patch("cv2.VideoCapture") as mock_vc:
            mock_capture = Mock()
            mock_capture.get.return_value = 30.0  # 30 fps
            mock_vc.return_value = mock_capture

            extractor = ThumbnailExtractor(
                video_path=video_path,
                template_path=template_path,
                resolution=3,
            )

            # 30 fps / 3 resolution = 10 (every 10th frame)
            assert extractor.frame_frequency() == 10


class TestHelperFunctions:
    """Test helper functions."""

    def test_get_default_thumbnail_template(self):
        """Test getting default thumbnail template path."""
        path = get_default_thumbnail_template()
        assert isinstance(path, Path)
        assert path.name == "thumbnail_template.png"

    def test_load_template_default(self):
        """Test loading default template."""
        # Should successfully load the bundled default template
        template = load_template(None)
        assert template is not None
        assert isinstance(template, np.ndarray)
        # Should be a valid image (height, width, channels)
        assert len(template.shape) == 3

    def test_load_template_custom(self, tmp_path):
        """Test loading custom template."""
        template_path = tmp_path / "custom_template.png"

        # Create dummy template
        template_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv.imwrite(str(template_path), template_img)

        loaded = load_template(template_path)
        assert loaded is not None
        assert isinstance(loaded, np.ndarray)

    def test_load_template_not_found(self, tmp_path):
        """Test loading non-existent template raises error."""
        # Test with explicit non-existent path
        with pytest.raises(FileNotFoundError):
            load_template(tmp_path / "nonexistent.png")

    def test_generate_default_output_path(self, tmp_path):
        """Test generating default output path."""
        video_path = Path("/path/to/video.mp4")

        # Mock Path.cwd() to return tmp_path
        with patch("pathlib.Path.cwd", return_value=tmp_path):
            output_path = generate_default_output_path(video_path)

            assert output_path.parent == tmp_path
            assert output_path.name == "video-thumbnail.jpg"

    def test_calculate_ssim_identical(self):
        """Test SSIM calculation with identical images."""
        # Create two identical images
        img1 = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img2 = img1.copy()

        score = calculate_ssim(img1, img2)

        # Identical images should have SSIM score of 1.0
        assert score == pytest.approx(1.0, abs=0.01)

    def test_calculate_ssim_different(self):
        """Test SSIM calculation with different images."""
        # Create two different images
        img1 = np.zeros((100, 100, 3), dtype=np.uint8)
        img2 = np.ones((100, 100, 3), dtype=np.uint8) * 255

        score = calculate_ssim(img1, img2)

        # Different images should have low SSIM score
        assert score < 0.5


class TestExtractThumbnail:
    """Test extract_thumbnail function."""

    def test_extract_thumbnail_success(self, tmp_path):
        """Test successful thumbnail extraction."""
        video_path = tmp_path / "test.mp4"
        template_path = tmp_path / "template.png"
        output_path = tmp_path / "output.jpg"

        # Create dummy template
        template_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv.imwrite(str(template_path), template_img)

        # Mock VideoCapture to simulate video frames
        with patch("loups.thumbnail_extractor.cv.VideoCapture") as mock_vc:
            mock_capture = Mock()
            mock_capture.get.side_effect = [
                30.0,  # frame_rate for initialization
                1000.0,  # timestamp_ms when we save
            ]

            # With resolution=30 and frame_rate=30, frame_interval = 30/30 = 1
            # So frame 1 % 1 == 0 (checks first frame)
            # Simulate first frame grab succeeds, second fails (end of video)
            mock_capture.grab.side_effect = [True, False]

            # Create a frame that matches the template
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_capture.retrieve.return_value = (True, frame)

            mock_vc.return_value = mock_capture

            # Extract with high threshold that will match identical images
            # Use resolution=30 so frame_interval = 1 (check every frame)
            result = extract_thumbnail(
                video_path=video_path,
                template_path=template_path,
                output_path=output_path,
                threshold=0.9,
                scan_duration=10,
                resolution=30,  # 30 fps / 30 resolution = interval of 1
            )

            assert result is not None
            assert isinstance(result, ThumbnailResult)
            assert result.success is True
            assert result.output_path == output_path

    def test_extract_thumbnail_no_match(self, tmp_path):
        """Test thumbnail extraction when no frame exceeds threshold."""
        video_path = tmp_path / "test.mp4"
        template_path = tmp_path / "template.png"

        # Create template (black image)
        template_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv.imwrite(str(template_path), template_img)

        with patch("loups.thumbnail_extractor.cv.VideoCapture") as mock_vc:
            mock_capture = Mock()
            mock_capture.get.return_value = 30.0  # frame_rate

            # Simulate 30 frames (with resolution=30, checks every frame)
            mock_capture.grab.side_effect = [True] * 30 + [False]

            # Return white frames (different from black template)
            white_frame = np.ones((100, 100, 3), dtype=np.uint8) * 255
            mock_capture.retrieve.return_value = (True, white_frame)

            mock_vc.return_value = mock_capture

            # Extract with high threshold (won't match)
            result = extract_thumbnail(
                video_path=video_path,
                template_path=template_path,
                threshold=0.9,  # High threshold won't match different images
                scan_duration=1,
                resolution=30,  # 30 fps / 30 resolution = interval of 1
            )

            # Should return None when no match found
            assert result is None

    def test_extract_thumbnail_default_output_path(self, tmp_path):
        """Test that default output path is generated correctly."""
        video_path = tmp_path / "mygame.mp4"
        template_path = tmp_path / "template.png"

        # Create template
        template_img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv.imwrite(str(template_path), template_img)

        with (
            patch("loups.thumbnail_extractor.cv.VideoCapture") as mock_vc,
            patch("pathlib.Path.cwd", return_value=tmp_path),
        ):
            mock_capture = Mock()
            mock_capture.get.side_effect = [30.0, 500.0]
            mock_capture.grab.side_effect = [True, False]
            frame = np.zeros((100, 100, 3), dtype=np.uint8)
            mock_capture.retrieve.return_value = (True, frame)
            mock_vc.return_value = mock_capture

            result = extract_thumbnail(
                video_path=video_path,
                template_path=template_path,
                output_path=None,  # No output path specified
                threshold=0.9,
                scan_duration=1,
                resolution=30,  # 30 fps / 30 resolution = interval of 1
            )

            assert result is not None
            # Default path should be <video>-thumbnail.jpg in cwd
            assert result.output_path == tmp_path / "mygame-thumbnail.jpg"
