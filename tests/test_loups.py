"""Loups pytest suite."""

import logging

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
