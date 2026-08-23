"""Determine which placement cells a footprint occupies.

The input footprint is assumed to be an exact union of whole 42mm
cells, but feet are placed on a finer PLACEMENT_CELL_SIZE_MM (21mm)
grid -- every 42mm cell splits into several independent feet. Since a
42mm cell is either wholly in or wholly out, every 21mm sub-cell within
it is too, so a single centroid point-in-polygon test per placement
cell is exact.
"""

from .constants import PLACEMENT_CELL_SIZE_MM
from .geometry import point_in_polygon


def rasterize(loops, grid_origin, cell_size=None):
    cell_size = cell_size or PLACEMENT_CELL_SIZE_MM
    xs = [p[0] for loop in loops for p in loop]
    ys = [p[1] for loop in loops for p in loop]
    max_x, max_y = max(xs), max(ys)
    ox, oy = grid_origin

    nx = max(1, round((max_x - ox) / cell_size))
    ny = max(1, round((max_y - oy) / cell_size))

    occupied = []
    for iy in range(ny):
        for ix in range(nx):
            cx = ox + ix * cell_size + cell_size / 2
            cy = oy + iy * cell_size + cell_size / 2
            if point_in_polygon((cx, cy), loops):
                occupied.append((ix, iy))
    return occupied, nx, ny
