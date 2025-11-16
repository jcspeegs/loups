"""Test constants for the loups test suite.

This module defines commonly used constants across tests to reduce
magic numbers and improve maintainability.
"""

# ============================================================================
# Video Constants
# ============================================================================

STANDARD_FPS = 30.0
"""Standard frames per second for test videos."""

FPS_60 = 60.0
"""60 frames per second (high frame rate)."""

FPS_15 = 15.0
"""15 frames per second (low frame rate)."""

FPS_29_97 = 29.97
"""29.97 frames per second (NTSC standard)."""


# ============================================================================
# Resolution/Sampling Constants
# ============================================================================

STANDARD_RESOLUTION = 3
"""Standard sampling resolution (frames per second to extract)."""

RESOLUTION_30 = 30
"""High sampling resolution (30 frames per second)."""


# ============================================================================
# Image Dimension Constants
# ============================================================================

TEMPLATE_DIMENSIONS = (100, 100, 3)
"""Standard template image dimensions (height, width, channels)."""

TEST_FRAME_DIMENSIONS = (100, 100, 3)
"""Standard test frame dimensions (height, width, channels)."""

LARGE_IMAGE_DIMENSIONS = (200, 200)
"""Large test image dimensions for match_template_scan tests."""

SMALL_TEMPLATE_DIMENSIONS = (50, 50)
"""Small template dimensions for match_template_scan tests."""


# ============================================================================
# Threshold Constants
# ============================================================================

HIGH_CONFIDENCE = 0.95
"""High confidence threshold for OCR results."""

STANDARD_CONFIDENCE = 0.88
"""Standard confidence threshold for OCR results."""

MATCH_SCORE_THRESHOLD = 0.85
"""Standard match score for FrameBatterInfo."""

SSIM_THRESHOLD_HIGH = 0.9
"""High SSIM threshold for image similarity."""

SSIM_THRESHOLD_STANDARD = 0.8
"""Standard SSIM threshold for image similarity."""


# ============================================================================
# OCR Test Data
# ============================================================================

SAMPLE_BATTER_NAMES = [
    "Jane Doe",
    "Sarah Johnson",
    "Emma Martinez",
    "Lily Garcia",
]
"""Common batter names used in tests."""

SAMPLE_JERSEY_NUMBERS = [
    "#7",
    "#12",
    "#21",
    "#34",
    "#42",
]
"""Common jersey numbers used in tests."""


# ============================================================================
# Timestamp Constants
# ============================================================================

TIMESTAMP_START = "0:00:00"
"""Standard starting timestamp."""

TIMESTAMP_MID_GAME = "0:05:23"
"""Mid-game timestamp for testing."""

TIMESTAMP_LATE_GAME = "0:08:45"
"""Late-game timestamp for testing."""
