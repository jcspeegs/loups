"""Loups pytest suite."""

import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import loups.loups as loups

logger = logging.getLogger(__name__)


class TestMilliSecond:
    """Tests for the loups.MilliSecond class."""

    @pytest.mark.parametrize(
        "ms, formatted_time",
        [
            (5_274_832.123, "01:27:54"),
            (636_987.987, "10:36"),
            (0.0, "00:00"),
            (0.99, "00:00"),
        ],
    )
    def test_millisecond_yt_format(self, ms, formatted_time):
        """Test MilliSecond class."""
        assert loups.MilliSecond(ms).yt_format() == formatted_time

    def test_millisecond_non_negatives(self):
        """No negative MilliSecond objects are valid.

        Test that a ValueError is raised with a custom message when a negative value is
        used to instantiate a Millisecond object.
        """
        invalid_millisecond = -1.0
        error_message_pattern = (
            rf"MilliSecond cannot be {str(invalid_millisecond)}, "
            "it must be a non-negative number."
        )
        with pytest.raises(ValueError, match=error_message_pattern):
            loups.MilliSecond(invalid_millisecond)


class TestBatterInfo:
    """Test TestBatterInfo class."""

    def test_first_batter_move_to_0000(self, list_frame_batter_info):
        """Test first chapter starts at 00:00 when batter starts less than 10s in."""
        display = loups.BatterInfo(list_frame_batter_info).display().split()
        logger.debug(f"{display=}")
        assert display[0] == "00:00"

    def test_intro_at_0000(self, list_frame_batter_info):
        """Test intro chapter gets inserted when first batter after 10 seconds in."""
        display = loups.BatterInfo(list_frame_batter_info[1:]).display().split("\n")
        logger.debug(f"{display=}")
        assert display[0] == "00:00 Game Time"


class TestBatterName:
    """Test the batter_name method to ensure '#' characters appear at end."""

    @pytest.mark.parametrize(
        "ocr_results, expected_output",
        [
            # Normal case: name + jersey number
            (
                [
                    ((0, 0, 100, 20), "Jane Doe", 0.95),
                    ((100, 0, 120, 20), "#12", 0.88),
                ],
                "Jane Doe #12",
            ),
            # Multiple '#' items - should all be at end
            (
                [
                    ((0, 0, 100, 20), "Jane Doe", 0.95),
                    ((100, 0, 120, 20), "#12", 0.88),
                    ((120, 0, 140, 20), "#34", 0.90),
                ],
                "Jane Doe #12 #34",
            ),
            # No '#' characters - just name
            (
                [
                    ((0, 0, 100, 20), "Jane", 0.95),
                    ((100, 0, 120, 20), "Doe", 0.88),
                ],
                "Jane Doe",
            ),
            # Only '#' items - no name text
            (
                [
                    ((0, 0, 50, 20), "#12", 0.88),
                    ((50, 0, 100, 20), "#34", 0.90),
                ],
                "#12 #34",
            ),
            # Mixed order: '#' items come first in OCR, should move to end
            (
                [
                    ((0, 0, 50, 20), "#12", 0.88),
                    ((50, 0, 150, 20), "Jane Doe", 0.95),
                ],
                "Jane Doe #12",
            ),
            # Low confidence score filtering (threshold=0.2)
            (
                [
                    ((0, 0, 100, 20), "Jane Doe", 0.95),
                    ((100, 0, 120, 20), "#12", 0.88),
                    ((120, 0, 140, 20), "noise", 0.15),  # Below threshold
                ],
                "Jane Doe #12",
            ),
            # Complex mixed order: '#' items scattered between name parts
            (
                [
                    ((0, 0, 50, 20), "Jane", 0.95),
                    ((50, 0, 70, 20), "#12", 0.88),
                    ((70, 0, 120, 20), "Doe", 0.92),
                    ((120, 0, 140, 20), "#34", 0.85),
                ],
                "Jane Doe #12 #34",
            ),
            # Empty OCR results
            (
                [],
                "",
            ),
            # All below threshold
            (
                [
                    ((0, 0, 100, 20), "text", 0.15),
                    ((100, 0, 120, 20), "#12", 0.10),
                ],
                "",
            ),
            # Single text element with jersey at start (THE BUG CASE)
            (
                [
                    ((0, 0, 200, 20), "#21 Lucy Del Toro", 0.89),
                ],
                "Lucy Del Toro #21",
            ),
            # Single text element with jersey in middle
            (
                [
                    ((0, 0, 200, 20), "Lucy #21 Del Toro", 0.89),
                ],
                "Lucy Del Toro #21",
            ),
            # Single text element with jersey already at end (should stay same)
            (
                [
                    ((0, 0, 200, 20), "Lucy Del Toro #21", 0.89),
                ],
                "Lucy Del Toro #21",
            ),
            # Multiple jerseys in single element
            (
                [
                    ((0, 0, 200, 20), "#12 Jane #34 Doe", 0.89),
                ],
                "Jane Doe #12 #34",
            ),
            # Mixed: some elements with embedded jerseys, some separate
            (
                [
                    ((0, 0, 100, 20), "#12 Jane", 0.95),
                    ((100, 0, 150, 20), "Doe", 0.92),
                    ((150, 0, 170, 20), "#34", 0.88),
                ],
                "Jane Doe #12 #34",
            ),
            # LEFT-TO-RIGHT ORDERING TESTS
            # Case 1: Last name returned before first name (Garcia Lily bug)
            (
                [
                    ([[116, 76], [270, 76], [270, 126], [116, 126]], "Garcia", 0.91),
                    ([[31, 131], [83, 131], [83, 167], [31, 167]], "#9", 0.99),
                    (
                        [
                            [29.8, 68.1],
                            [121.4, 81.1],
                            [111.2, 140.9],
                            [19.6, 127.9],
                        ],
                        "Lily",
                        0.99,
                    ),
                ],
                "Lily Garcia #9",
            ),
            # Case 2: Simple reversed first/last name
            (
                [
                    ((100, 0, 150, 20), "Smith", 0.95),
                    ((10, 0, 60, 20), "John", 0.93),
                    ((160, 0, 180, 20), "#42", 0.88),
                ],
                "John Smith #42",
            ),
            # Case 3: Three name parts out of order
            (
                [
                    ((100, 0, 150, 20), "Middle", 0.95),
                    ((0, 0, 50, 20), "First", 0.93),
                    ((160, 0, 210, 20), "Last", 0.92),
                    ((220, 0, 240, 20), "#7", 0.88),
                ],
                "First Middle Last #7",
            ),
            # Case 4: Jersey number positioned before name but returned after
            (
                [
                    ((50, 0, 150, 20), "Jane Doe", 0.95),
                    ((10, 0, 40, 20), "#15", 0.88),
                ],
                "Jane Doe #15",
            ),
            # Case 5: All elements in reverse order
            (
                [
                    ((200, 0, 220, 20), "#33", 0.88),
                    ((120, 0, 180, 20), "Last", 0.92),
                    ((60, 0, 100, 20), "Middle", 0.93),
                    ((0, 0, 50, 20), "First", 0.95),
                ],
                "First Middle Last #33",
            ),
        ],
    )
    def test_batter_name_ensures_hash_at_end(self, ocr_results, expected_output):
        """Test that batter_name always places '#' characters at the end.

        This test mocks the EasyOCR reader to return controlled test data,
        then verifies that:
        1. Text elements are sorted left-to-right by x-coordinate
        2. Items containing '#' are moved to the end of the result
        3. Confidence threshold filtering works correctly (default 0.2)
        4. Results are joined with spaces

        The left-to-right sorting ensures that names appear in the correct
        order regardless of OCR's internal detection order (e.g., prevents
        "Garcia Lily" when the screen shows "Lily Garcia").
        """
        with patch.object(loups.Loups, "reader") as mock_reader:
            # Configure the mock to return our test OCR results
            mock_reader.readtext.return_value = ocr_results

            # Create a mock Loups instance with required attributes
            loups_instance = MagicMock(spec=["template", "frame"])

            # Mock the template as a 2D numpy array with shape (height, width)
            # Size namedtuple expects exactly 2 values: (height, width)
            loups_instance.template = np.zeros((100, 500), dtype=np.uint8)

            # Mock the frame as a numpy array that supports slicing
            # Make it large enough for any slice operation
            loups_instance.frame = np.zeros((1000, 1000), dtype=np.uint8)

            # Call the actual batter_name method with our mocked instance
            result = loups.Loups.batter_name(
                loups_instance, match_top_left=loups.Point(0, 0), threshold=0.2
            )

            # Verify the result matches expected output
            assert result == expected_output
