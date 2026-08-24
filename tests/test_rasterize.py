import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gfbadjust.rasterize import rasterize


class TestRasterize(unittest.TestCase):
    def test_simple_rectangle(self):
        # 2 cells wide x 1 cell tall, at origin (0,0)
        loop = [(0.0, 0.0), (84.0, 0.0), (84.0, 42.0), (0.0, 42.0)]
        occupied, nx, ny = rasterize([loop], (0.0, 0.0), cell_size=42.0)
        self.assertEqual(nx, 2)
        self.assertEqual(ny, 1)
        self.assertEqual(set(occupied), {(0, 0), (1, 0)})

    def test_l_shape_excludes_missing_corner(self):
        # 2x2 block missing the top-right cell (1,1)
        loop = [
            (0.0, 0.0), (84.0, 0.0), (84.0, 42.0),
            (42.0, 42.0), (42.0, 84.0), (0.0, 84.0),
        ]
        occupied, nx, ny = rasterize([loop], (0.0, 0.0), cell_size=42.0)
        self.assertEqual(set(occupied), {(0, 0), (1, 0), (0, 1)})
        self.assertNotIn((1, 1), set(occupied))

    def test_default_cell_size_splits_one_42mm_cell_into_four(self):
        # A single 42mm cell should rasterize (at the default 21mm
        # placement resolution) into a 2x2 block of four sub-cells.
        loop = [(0.0, 0.0), (42.0, 0.0), (42.0, 42.0), (0.0, 42.0)]
        occupied, nx, ny = rasterize([loop], (0.0, 0.0))
        self.assertEqual((nx, ny), (2, 2))
        self.assertEqual(set(occupied), {(0, 0), (1, 0), (0, 1), (1, 1)})

    def test_multi_island_footprint_covers_full_extent(self):
        # Three separate, similarly-sized loops (independent per-cell
        # blocks, not one continuous body) tiling a 2x2 area. The full
        # extent must be detected from all of them together, not just
        # whichever single loop happens to be largest -- otherwise most
        # of the footprint silently gets no base at all.
        cell_a = [(0.0, 0.0), (41.5, 0.0), (41.5, 41.5), (0.0, 41.5)]
        cell_b = [(42.0, 0.0), (83.5, 0.0), (83.5, 41.5), (42.0, 41.5)]
        cell_c = [(0.0, 42.0), (41.5, 42.0), (41.5, 83.5), (0.0, 83.5)]
        occupied, nx, ny = rasterize(
            [cell_a, cell_b, cell_c], (-0.25, -0.25), cell_size=42.0
        )
        self.assertEqual((nx, ny), (2, 2))
        self.assertEqual(set(occupied), {(0, 0), (1, 0), (0, 1)})
        self.assertNotIn((1, 1), set(occupied))


if __name__ == "__main__":
    unittest.main()
