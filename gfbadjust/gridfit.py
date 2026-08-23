"""Derive the 42mm grid origin from a whole-cell footprint's bounding box."""

from .constants import GRID_DIMENSIONS_MM


def compute_grid_origin(loops, cell_size=None):
    cell_size = cell_size or GRID_DIMENSIONS_MM[0]
    xs = [p[0] for loop in loops for p in loop]
    ys = [p[1] for loop in loops for p in loop]
    min_x, min_y = min(xs), min(ys)
    origin_x = round(min_x / cell_size) * cell_size
    origin_y = round(min_y / cell_size) * cell_size
    return (origin_x, origin_y)
