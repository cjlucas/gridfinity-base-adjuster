"""Reusable correctness checks for gfladjust outputs.

Mirrors invariants.py's approach: properties that must hold for ANY
valid input/output pair, not exact-match assertions about one specific
fixture's expected geometry.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from invariants import InvariantError, check_xy_bbox_preserved  # noqa: F401 -- re-exported

__all__ = ["InvariantError", "check_xy_bbox_preserved", "check_output_height"]


def check_output_height(input_mesh, output_mesh, expected_lip_height, tol=0.05):
    """The output must be exactly the input, minus the detected lip.

    Catches a wrong cut height (too much or too little of the lip
    removed) and catches the bottom/base accidentally being touched.
    """
    (_, _, in_min_z), (_, _, in_max_z) = input_mesh.bbox()
    (_, _, out_min_z), (_, _, out_max_z) = output_mesh.bbox()

    if abs(in_min_z - out_min_z) > tol:
        raise InvariantError(
            f"output's bottom moved: input min_z={in_min_z:.3f}, "
            f"output min_z={out_min_z:.3f} -- lip removal must never touch the base"
        )

    expected_max_z = in_max_z - expected_lip_height
    if abs(out_max_z - expected_max_z) > tol:
        raise InvariantError(
            f"output max_z={out_max_z:.3f}, expected {expected_max_z:.3f} "
            f"(input max_z={in_max_z:.3f} minus {expected_lip_height:.3f}mm lip)"
        )
    return out_max_z
