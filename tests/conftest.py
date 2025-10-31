"""Configure pytest for loups."""

import pytest

import loups.loups as loups


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
