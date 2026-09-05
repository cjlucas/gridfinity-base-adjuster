"""Auto-detect a Gridfinity stacking lip's height from mesh geometry alone.

No --lip-height flag exists (deliberate -- see constants.py); this
module IS the detection logic, so getting it right matters.

Approach: Gridfinity bin heights are built from a fixed 7mm vertical
unit (e.g. a 6-unit bin's base+walls sum to exactly 42mm -- confirmed
against gf-rebuilt-bin-*-0bf37.stl, a known lip-less reference file),
and a stacking lip is *purely additive* height on top of that. Confirmed
two ways: (a) directly, by comparing a lipped/lip-less reference pair
(gf-rebuilt-bin-*-21fbb.stl vs *-0bf37.stl) -- the lipped file's total
height is exactly 3.5514717mm more than a clean 7mm-unit multiple; (b)
against kennetek/gridfinity-rebuilt-openscad's own source (almost
certainly the generator behind both sample files, going by their
filenames) -- its STACKING_LIP_LINE = [[0,0],[0.7,0.7],[0.7,2.5],
[2.6,4.4]] gives a nominal 4.4mm lip, reduced to ~3.55mm by a 0.6mm tip
fillet ("preventing sharp points" per that project), matching (a)
exactly.

So: total mesh height modulo the 7mm unit gives a strong,
generator-agnostic candidate lip height, with NO cross-sectional
geometry analysis needed as the *primary* signal. A cross-sectional
check is still used below to *confirm* the candidate isn't just a
coincidentally unit-aligned height with no real lip -- but it has to
look at both the outer wall AND the inner bore, not just one:

- gridfinity-rebuilt-openscad's lip (above) is mostly an INNER bore/
  cavity shelf, with only a small outer-wall dip right at the very tip
  (from its 0.6mm fillet).
- A second real-world file (a "Field Notes holder" bin, of unknown
  generator -- see tests/fixtures/lip_regression_corpus/) has a lip
  whose OUTER wall never moves at all (flat to within 0.02mm of the
  top), but whose INNER bore shows an unmistakable, sharp transition
  (~123mm to ~102mm within 0.01mm of Z) exactly at the mod-7 candidate
  cut height. An outer-only confirmation check flagged this real lip as
  "coincidental" and refused to remove it -- a false negative found via
  a real file, not speculation, so per this project's testing strategy
  the check below now looks at inner bore too, not just outer.

Checking the inner bore is NOT simply "does it return to a stable
baseline" (see below): a bin's inner cavity can vary with height for
reasons that have nothing to do with a lip (e.g. the gf-rebuilt "1x1x6"
reference bins have a scooped/tapered interior, so their inner bore
differs from each other even at mid-wall height, far from top or
bottom). Instead, both checks below compare a sample near the very top
against a sample just below the candidate cut plane -- looking for A
transition existing near the top at all, not for either endpoint
matching some absolute expected value. Confirmation passes if EITHER
the outer wall OR the pooled inner-hole loops show a big-enough change
between those two samples.

Known limitation (documented, not solved): a coincidentally
unit-aligned height on a file that ALSO happens to have some unrelated
inner feature near the top (a scallop, a label slot) could in principle
still false-positive here. No real file has hit this yet -- if one does,
that's the next thing to fix (see CLAUDE.md's testing strategy: real
files, not speculation, drive this).
"""

from gfbadjust import slicing
from gfbadjust.geometry import all_loops_bbox, loop_bbox, main_loop

from .constants import (
    CONFIRM_MIN_WIDTH_DELTA_MM,
    CONFIRM_SAMPLE_BELOW_CUT_MM,
    CONFIRM_SAMPLE_NEAR_TOP_MM,
    LIP_HEIGHT_MAX_MM,
    LIP_HEIGHT_MIN_MM,
    UNIT_HEIGHT_MM,
)


class LipDetectionError(Exception):
    pass


def _outer_and_hole_width(mesh, z):
    """(outer wall width, pooled inner-hole width) at height z.

    Either element is None if there's no material / no hole loop at
    that height. main_loop() (the biggest-bbox-area loop) is the right
    tool for "the outer wall" -- exactly what its own docstring says
    it's for. The remaining loops are pooled with all_loops_bbox rather
    than picking the single biggest one, so a multi-compartment bin's
    lip (one continuous opening at the rim, possibly several separate
    compartment loops lower down) is measured consistently either way.
    """
    loops = slicing.plane_slice(mesh, z)
    if not loops:
        return None, None
    outer = main_loop(loops)
    min_x, min_y, max_x, max_y = loop_bbox(outer)
    outer_width = max(max_x - min_x, max_y - min_y)

    holes = [l for l in loops if l is not outer]
    if not holes:
        return outer_width, None
    min_x, min_y, max_x, max_y = all_loops_bbox(holes)
    hole_width = max(max_x - min_x, max_y - min_y)
    return outer_width, hole_width


def detect_lip_height(mesh, verbose=False):
    """Return the detected lip height in mm, or 0.0 if no lip is present.

    Raises LipDetectionError if the height doesn't plausibly indicate a
    lip, or a lip-shaped remainder is found but no geometric transition
    confirms it near the top.
    """
    (_, _, min_z), (_, _, max_z) = mesh.bbox()
    total_height = max_z - min_z

    remainder = total_height % UNIT_HEIGHT_MM
    if verbose:
        units = int(total_height // UNIT_HEIGHT_MM)
        print(
            f"total height {total_height:.4f}mm = {units} x {UNIT_HEIGHT_MM}mm "
            f"units + {remainder:.4f}mm"
        )

    if remainder < LIP_HEIGHT_MIN_MM:
        return 0.0

    if remainder > LIP_HEIGHT_MAX_MM:
        raise LipDetectionError(
            f"total height {total_height:.4f}mm isn't close to a clean "
            f"{UNIT_HEIGHT_MM}mm-unit multiple (remainder {remainder:.4f}mm, "
            f"outside the {LIP_HEIGHT_MIN_MM}-{LIP_HEIGHT_MAX_MM}mm plausible "
            "lip-height range) -- can't confidently auto-detect a stacking lip"
        )

    lip_cut_z = max_z - remainder

    near_top_outer, near_top_hole = _outer_and_hole_width(mesh, max_z - CONFIRM_SAMPLE_NEAR_TOP_MM)
    below_cut_outer, below_cut_hole = _outer_and_hole_width(mesh, lip_cut_z - CONFIRM_SAMPLE_BELOW_CUT_MM)
    if near_top_outer is None or below_cut_outer is None:
        raise LipDetectionError(
            "couldn't slice near the detected lip boundary to confirm it"
        )

    outer_changed = abs(near_top_outer - below_cut_outer) >= CONFIRM_MIN_WIDTH_DELTA_MM
    hole_changed = (
        near_top_hole is not None
        and below_cut_hole is not None
        and abs(near_top_hole - below_cut_hole) >= CONFIRM_MIN_WIDTH_DELTA_MM
    )
    if not (outer_changed or hole_changed):
        raise LipDetectionError(
            f"height {total_height:.4f}mm looks like a {UNIT_HEIGHT_MM}mm-unit "
            f"bin plus a {remainder:.4f}mm lip, but neither the wall's outer "
            "footprint nor its inner bore actually change near the top -- this "
            "looks like a coincidentally unit-aligned height rather than a "
            "real stacking lip, refusing to guess"
        )

    if verbose:
        print(f"detected stacking lip: {remainder:.4f}mm (cut at z={lip_cut_z:.4f})")

    return remainder
