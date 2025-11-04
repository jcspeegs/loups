"""Geometric types for spatial operations on images and frames."""

from collections import namedtuple

Point = namedtuple("Point", "x, y")
Size = namedtuple("Size", "height, width")
