"""Geometric types for spatial operations on images and frames.

This module provides lightweight namedtuple types for representing
2D coordinates and dimensions in image processing operations.

Types:
    Point: A 2D coordinate with x and y attributes.
    Size: Image dimensions with height and width attributes.

Examples:
    ```python
    from loups.geometry import Point, Size

    # Create a point
    top_left = Point(x=100, y=200)
    print(top_left.x, top_left.y)  # 100 200

    # Create a size
    frame_size = Size(height=1080, width=1920)
    print(frame_size.height, frame_size.width)  # 1080 1920
    ```
"""

from collections import namedtuple

Point = namedtuple("Point", "x, y")
"""2D coordinate point with x and y attributes."""

Size = namedtuple("Size", "height, width")
"""Image dimensions with height and width attributes."""
