"""Shared utilities for frame processing and sampling."""


def calculate_frame_frequency(frame_rate: float, resolution: int) -> int:
    """
    Calculate how often to sample frames based on desired resolution.

    Args:
        frame_rate: Video frame rate (fps)
        resolution: Desired frames to process per second

    Returns:
        Frame interval (process every Nth frame)

    Example:
        Video at 30fps, resolution=3 → return 10 (every 10th frame)
    """
    return int(frame_rate / resolution)
