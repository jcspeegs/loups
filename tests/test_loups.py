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
