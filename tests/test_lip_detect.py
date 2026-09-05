import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gfbadjust.stl_io import Mesh
from gfladjust.lip_detect import LipDetectionError, detect_lip_height


def box_triangles(x0, y0, z0, x1, y1, z1):
    # 8 corners
    c = {
        (0, 0, 0): (x0, y0, z0), (1, 0, 0): (x1, y0, z0),
        (1, 1, 0): (x1, y1, z0), (0, 1, 0): (x0, y1, z0),
        (0, 0, 1): (x0, y0, z1), (1, 0, 1): (x1, y0, z1),
        (1, 1, 1): (x1, y1, z1), (0, 1, 1): (x0, y1, z1),
    }
    quads = [
        [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)],  # bottom
        [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],  # top
        [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)],  # y0 wall
        [(1, 1, 0), (0, 1, 0), (0, 1, 1), (1, 1, 1)],  # y1 wall
        [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)],  # x0 wall
        [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)],  # x1 wall
    ]
    triangles = []
    for quad in quads:
        p0, p1, p2, p3 = (c[k] for k in quad)
        triangles.append((p0, p1, p2))
        triangles.append((p0, p2, p3))
    return triangles


def hollow_box_with_inner_lip_triangles(size, wall_height, lip_height, wall_thick, lip_wall_thick):
    """Outer footprint never changes; the *inner* cavity steps to a much
    narrower bore for the top lip_height mm (thicker "wall" up there).

    Regression fixture for a real bug: a real-world bin (a "Field Notes
    holder", see tests/fixtures/lip_regression_corpus/) has a lip whose
    outer wall never moves at all -- only the inner bore shows the
    transition. An outer-only confirmation check misses this entirely.
    This doesn't need real CSG: plane_slice only cares about loop
    geometry, so unioning a separate, smaller "inner boundary" box's
    triangles alongside the outer shell's (rather than actually
    subtracting one from the other) produces the same slice loops --
    same technique test_slicing.py's test_two_disjoint_boxes uses for a
    second loop.
    """
    outer = box_triangles(0, 0, 0, size, size, wall_height + lip_height)
    lower_hole = box_triangles(
        wall_thick, wall_thick, 0,
        size - wall_thick, size - wall_thick, wall_height,
    )
    upper_hole = box_triangles(
        lip_wall_thick, lip_wall_thick, wall_height,
        size - lip_wall_thick, size - lip_wall_thick, wall_height + lip_height,
    )
    return outer + lower_hole + upper_hole


def box_with_lip_triangles(size, wall_height, lip_height, lip_inset):
    """A plain box topped with a smaller box -- stands in for a real
    lip's outer-footprint dip near the tip without reproducing the
    exact real profile (see gfladjust/lip_detect.py's module docstring
    for why the real mechanism is more subtle, and why this is still a
    valid test of the detector's actual logic: mod-7 remainder + an
    outer-footprint transition near the top)."""
    bottom = box_triangles(0, 0, 0, size, size, wall_height)
    top = box_triangles(
        lip_inset, lip_inset, wall_height,
        size - lip_inset, size - lip_inset, wall_height + lip_height,
    )
    return bottom + top


class TestLipDetect(unittest.TestCase):
    def test_detects_lip_height(self):
        mesh = Mesh(box_with_lip_triangles(size=40, wall_height=42, lip_height=3.6, lip_inset=1.0))
        self.assertAlmostEqual(detect_lip_height(mesh), 3.6, places=3)

    def test_no_lip_on_clean_unit_multiple(self):
        mesh = Mesh(box_triangles(0, 0, 0, 40, 40, 42))
        self.assertEqual(detect_lip_height(mesh), 0.0)

    def test_refuses_coincidental_unit_aligned_height(self):
        # Same total height as test_detects_lip_height's fixture (42 +
        # 3.6 = 45.6), but perfectly flat the whole way -- must not be
        # mistaken for a real lip just because the remainder looks
        # plausible. Regression test for the confirmation check.
        mesh = Mesh(box_triangles(0, 0, 0, 40, 40, 45.6))
        with self.assertRaises(LipDetectionError):
            detect_lip_height(mesh)

    def test_refuses_implausible_remainder(self):
        mesh = Mesh(box_triangles(0, 0, 0, 40, 40, 42 + 6.5))
        with self.assertRaises(LipDetectionError):
            detect_lip_height(mesh)

    def test_detects_inner_only_lip(self):
        # Outer footprint is constant the whole way -- only the inner
        # bore steps at the lip boundary. Must not be missed just
        # because the outer wall never changes (see the fixture's
        # docstring for the real-world bug this guards against).
        mesh = Mesh(hollow_box_with_inner_lip_triangles(
            size=40, wall_height=42, lip_height=3.8, wall_thick=2, lip_wall_thick=12,
        ))
        self.assertAlmostEqual(detect_lip_height(mesh), 3.8, places=3)


if __name__ == "__main__":
    unittest.main()
