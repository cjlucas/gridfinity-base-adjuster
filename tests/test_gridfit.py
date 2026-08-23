import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gfbadjust.gridfit import compute_grid_origin


class TestGridfit(unittest.TestCase):
    def test_origin_at_zero(self):
        loop = [(0.0, 0.0), (84.0, 0.0), (84.0, 42.0), (0.0, 42.0)]
        self.assertEqual(compute_grid_origin([loop]), (0.0, 0.0))

    def test_origin_at_offset_multiple(self):
        loop = [(84.0, 126.0), (168.0, 126.0), (168.0, 210.0), (84.0, 210.0)]
        self.assertEqual(compute_grid_origin([loop]), (84.0, 126.0))

    def test_origin_with_floating_point_noise(self):
        loop = [
            (84.00003, 125.99998),
            (168.00001, 125.99998),
            (168.00001, 210.00002),
            (84.00003, 210.00002),
        ]
        origin = compute_grid_origin([loop])
        self.assertAlmostEqual(origin[0], 84.0)
        self.assertAlmostEqual(origin[1], 126.0)


if __name__ == "__main__":
    unittest.main()
