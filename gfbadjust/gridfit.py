"""Derive the 42mm grid origin from a whole-cell footprint's bounding box."""

from .constants import BASE_GAP_MM
from .geometry import all_loops_bbox


def compute_grid_origin(loops, cell_size=None):
    # Deliberately NOT snapped to a global multiple of cell_size from world
    # (0,0) -- a footprint can sit at any arbitrary offset in its own file
    # (e.g. a hand-placed custom holder), so the grid this object uses has
    # no reason to align with an external/global frame. Instead, trust the
    # footprint's own bbox corner directly: since the footprint is assumed
    # to be an exact union of whole cells, that corner IS a true cell
    # boundary, just inset by half the inter-cell gap from the nominal
    # grid line (the same convention applied when the foot geometry itself
    # is built), which is corrected for here.
    #
    # Uses the bbox across ALL loops, not just the largest one -- a
    # footprint can be made of several separate same-size islands (see
    # geometry.main_loop's docstring), and picking only the biggest would
    # silently truncate the detected footprint to a fraction of the real
    # one.
    min_x, min_y, _, _ = all_loops_bbox(loops)
    half_gap = BASE_GAP_MM / 2
    return (min_x - half_gap, min_y - half_gap)
