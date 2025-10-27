"""Loups pytest suite."""

import pytest

import loups.loups as loups


@pytest.mark.parametrize(
    "ms, formatted_time",
    [
        (5_274_832, "01:27:54"),
        (0, "00:00:00"),
    ],
)
def test_millisecond_yt_format(ms, formatted_time):
    """Test MilliSecond class."""
    assert loups.MilliSecond(ms).yt_format() == formatted_time


def test_millisecond_non_negatives():
    """No negative MilliSecond objects are valid.

    Test that a ValueError is raised with a custom message when a negative Millisecond
    object is attempted.
    """
    invalid_millisecond = -1.0
    error_message_pattern = (
        rf"MilliSecond cannot be {str(invalid_millisecond)}, "
        "it must be a non-negative number."
    )
    with pytest.raises(ValueError, match=error_message_pattern):
        loups.MilliSecond(invalid_millisecond)
