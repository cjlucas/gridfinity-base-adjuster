"""Determine which placement cells a footprint occupies.

The input footprint is assumed to be an exact union of whole 42mm
cells, but feet are placed on a finer PLACEMENT_CELL_SIZE_MM (21mm)
grid -- every 42mm cell splits into several independent feet. Since a
42mm cell is either wholly in or wholly out, every 21mm sub-cell within
it is too, so in principle a single centroid point-in-polygon test per
placement cell is exact.

In practice a single centroid sample is fragile: the footprint is
sliced 0.2mm above the cut plane specifically to read the shape of the
body sitting on the base, and a real body's floor right there isn't
always flat. A confirmed real case: a bin whose interior floor is
scalloped/egg-crate shaped (four rounded troughs meeting at points),
where the low point of a trough landed almost exactly on a placement
cell's centroid -- the slice at that height is genuinely void there,
even though the cell as a whole is fully supported by solid base
underneath. (A small magnet/screw hole bored through a cell center
would hit the same failure mode via the even-odd rule seeing "inside
two loops" and canceling to "not inside", though that hasn't been the
observed cause in practice.) Sampling several points around the
centroid and going with the majority survives a local void at (or near)
dead center while still being exact for the normal fully-flat case,
where every sample agrees.
"""

from .constants import PLACEMENT_CELL_SIZE_MM
from .geometry import all_loops_bbox, point_in_polygon

# Offset (as a fraction of cell_size) of the four off-center samples from
# the cell's centroid. 1/4 of a 21mm cell is ~5.25mm from center -- well
# clear of small local voids (a magnet/screw hole, a rounded trough
# bottom, etc.) a few mm across, while still staying safely inside the
# cell away from its boundary.
SAMPLE_OFFSET_FRACTION = 0.25


def _sample_points(cx, cy, cell_size):
    offset = cell_size * SAMPLE_OFFSET_FRACTION
    return [
        (cx, cy),
        (cx + offset, cy),
        (cx - offset, cy),
        (cx, cy + offset),
        (cx, cy - offset),
    ]


def rasterize(loops, grid_origin, cell_size=None):
    cell_size = cell_size or PLACEMENT_CELL_SIZE_MM
    # Grid extent comes from the bbox across ALL loops -- a footprint can
    # be made of several separate same-size islands (see
    # geometry.main_loop's docstring), so using only the single largest
    # loop would silently truncate the detected grid to a fraction of
    # the real footprint. The occupancy test below checks against every
    # loop regardless, so holes/dividers are still correctly respected
    # as gaps via the even-odd rule.
    _, _, max_x, max_y = all_loops_bbox(loops)
    ox, oy = grid_origin

    nx = max(1, round((max_x - ox) / cell_size))
    ny = max(1, round((max_y - oy) / cell_size))

    occupied = []
    for iy in range(ny):
        for ix in range(nx):
            cx = ox + ix * cell_size + cell_size / 2
            cy = oy + iy * cell_size + cell_size / 2
            samples = _sample_points(cx, cy, cell_size)
            inside = sum(point_in_polygon(p, loops) for p in samples)
            if inside > len(samples) / 2:
                occupied.append((ix, iy))
    return occupied, nx, ny
