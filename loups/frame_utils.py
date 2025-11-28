"""Shared utilities for frame processing and sampling.

This module provides helper functions for calculating frame sampling rates
to optimize video processing performance.
"""


def calculate_frame_frequency(frame_rate: float, resolution: int) -> int:
    """Calculate how often to sample frames based on desired resolution.

    Args:
        frame_rate: Video frame rate (fps).
        resolution: Desired frames to process per second.

    Returns:
        Frame interval (process every Nth frame).

    Examples:
        ```python
        # Video at 30fps, sample 3 frames per second
        interval = calculate_frame_frequency(30.0, 3)
        print(interval)  # 10 (every 10th frame)

        # Video at 60fps, sample 6 frames per second
        interval = calculate_frame_frequency(60.0, 6)
        print(interval)  # 10 (every 10th frame)
        ```
    """
    return int(frame_rate / resolution)
