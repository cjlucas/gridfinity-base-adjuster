"""Reusable correctness checks for gfbadjust outputs.

These encode invariants that should hold for ANY valid input, not
expected geometry specific to one fixture -- used by both the
synthetic-fixture end-to-end test and ad hoc checks against real-world
files (see check_output.py).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gfbadjust import slicing
from gfbadjust.geometry import loop_bbox

# The real max width of a 21mm sub-foot tops out around 20.5mm (top
# island = 21 - BASE_GAP_MM); a wider loop near the bottom means a
# leftover 42mm-scale foot survived somehow.
MAX_SUBFOOT_WIDTH_MM = 25.0


class InvariantError(AssertionError):
    pass


def feet_near_bottom(mesh, at_height=0.5):
    (min_x, min_y, min_z), _ = mesh.bbox()
    loops = slicing.plane_slice(mesh, min_z + at_height)
    if not loops:
        raise InvariantError(f"no loops found {at_height}mm above the mesh's minimum Z")
    return loops


def check_all_feet_are_21mm_scale(mesh, at_height=0.5):
    """No 42mm-scale foot should ever survive in the output.

    Catches the "old base wasn't actually cut away" bug class -- e.g. a
    clip box that missed the model because it was hardcoded near world
    origin (commit e3e1334).
    """
    loops = feet_near_bottom(mesh, at_height)
    max_width = max(loop_bbox(l)[2] - loop_bbox(l)[0] for l in loops)
    if max_width >= MAX_SUBFOOT_WIDTH_MM:
        raise InvariantError(
            f"found a foot {max_width:.1f}mm wide near the bottom -- expected "
            f"all feet to be <{MAX_SUBFOOT_WIDTH_MM}mm (21mm-scale)"
        )
    return max_width


def check_foot_count(mesh, expected_count, at_height=0.5):
    """The right NUMBER of feet must be present.

    Catches footprint detection silently truncating to a fraction of the
    real footprint -- e.g. a multi-island bin where only one "main" loop
    got measured (commit 7e867b4), or a bad --base-height skipping cells.
    """
    loops = feet_near_bottom(mesh, at_height)
    if len(loops) != expected_count:
        raise InvariantError(
            f"found {len(loops)} feet near the bottom, expected {expected_count}"
        )
    return len(loops)


def check_xy_bbox_preserved(input_mesh, output_mesh, tol=0.5):
    """The output's footprint must match the input's in X/Y.

    Catches the new base overhanging or shrinking relative to the
    original body -- e.g. a mis-detected grid origin (commit 8d9b87f).
    """
    (in_min_x, in_min_y, _), (in_max_x, in_max_y, _) = input_mesh.bbox()
    (out_min_x, out_min_y, _), (out_max_x, out_max_y, _) = output_mesh.bbox()
    diffs = {
        "min_x": abs(in_min_x - out_min_x),
        "min_y": abs(in_min_y - out_min_y),
        "max_x": abs(in_max_x - out_max_x),
        "max_y": abs(in_max_y - out_max_y),
    }
    bad = {k: v for k, v in diffs.items() if v > tol}
    if bad:
        raise InvariantError(
            f"output XY bbox differs from input by more than {tol}mm: {bad} -- "
            f"input=({in_min_x:.2f},{in_min_y:.2f})-({in_max_x:.2f},{in_max_y:.2f}) "
            f"output=({out_min_x:.2f},{out_min_y:.2f})-({out_max_x:.2f},{out_max_y:.2f})"
        )
