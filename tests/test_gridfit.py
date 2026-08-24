import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gfbadjust.gridfit import compute_grid_origin

HALF_GAP = 0.25  # BASE_GAP_MM / 2


class TestGridfit(unittest.TestCase):
    def test_origin_at_zero(self):
        # Visible footprint edge sits HALF_GAP inside the nominal grid line.
        loop = [
            (HALF_GAP, HALF_GAP), (84.0 + HALF_GAP, HALF_GAP),
            (84.0 + HALF_GAP, 42.0 + HALF_GAP), (HALF_GAP, 42.0 + HALF_GAP),
        ]
        origin = compute_grid_origin([loop])
        self.assertAlmostEqual(origin[0], 0.0)
        self.assertAlmostEqual(origin[1], 0.0)

    def test_origin_at_arbitrary_offset(self):
        # A footprint positioned nowhere near a clean multiple of 42 from
        # world (0,0) -- e.g. a hand-placed custom holder. The origin must
        # come from the footprint's own bbox, not a global grid snap.
        nominal_x, nominal_y = 86.0, 44.0
        loop = [
            (nominal_x + HALF_GAP, nominal_y + HALF_GAP),
            (nominal_x + 84.0 - HALF_GAP, nominal_y + HALF_GAP),
            (nominal_x + 84.0 - HALF_GAP, nominal_y + 42.0 - HALF_GAP),
            (nominal_x + HALF_GAP, nominal_y + 42.0 - HALF_GAP),
        ]
        origin = compute_grid_origin([loop])
        self.assertAlmostEqual(origin[0], nominal_x)
        self.assertAlmostEqual(origin[1], nominal_y)

    def test_small_internal_loop_doesnt_extend_origin(self):
        # A small hole/slot loop strictly inside the main outline can't
        # push the bbox corner further out, so it shouldn't change the
        # detected origin.
        main = [
            (HALF_GAP, HALF_GAP), (84.0 + HALF_GAP, HALF_GAP),
            (84.0 + HALF_GAP, 42.0 + HALF_GAP), (HALF_GAP, 42.0 + HALF_GAP),
        ]
        small_hole = [(40.0, 20.0), (41.0, 20.0), (41.0, 21.0), (40.0, 21.0)]
        origin = compute_grid_origin([main, small_hole])
        self.assertAlmostEqual(origin[0], 0.0)
        self.assertAlmostEqual(origin[1], 0.0)

    def test_multi_island_footprint_uses_full_extent(self):
        # A footprint built from several separate, similarly-sized blocks
        # (e.g. independent per-cell compartments with gaps between them)
        # rather than one continuous body -- no single loop represents
        # the whole footprint, so the origin must come from ALL of them,
        # not just whichever one happens to be biggest.
        cell_a = [(0.0, 0.0), (41.5, 0.0), (41.5, 41.5), (0.0, 41.5)]
        cell_b = [(42.0, 0.0), (83.5, 0.0), (83.5, 41.5), (42.0, 41.5)]
        cell_c = [(0.0, 42.0), (41.5, 42.0), (41.5, 83.5), (0.0, 83.5)]
        origin = compute_grid_origin([cell_a, cell_b, cell_c])
        self.assertAlmostEqual(origin[0], 0.0 - HALF_GAP)
        self.assertAlmostEqual(origin[1], 0.0 - HALF_GAP)


if __name__ == "__main__":
    unittest.main()
