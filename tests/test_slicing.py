import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gfbadjust.slicing import plane_slice
from gfbadjust.stl_io import Mesh


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


def loop_point_set(loop, precision=5):
    return {(round(x, precision), round(y, precision)) for (x, y) in loop}


def polygon_area(loop):
    # Shoelace formula. The wall faces are diagonally split, so a slice
    # exactly through a diagonal's crossing height legitimately produces
    # extra colinear vertices on straight edges -- area is what actually
    # matters, not the raw point count.
    area = 0.0
    n = len(loop)
    for i in range(n):
        x1, y1 = loop[i]
        x2, y2 = loop[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return abs(area) / 2.0


class TestSlicing(unittest.TestCase):
    def test_single_box(self):
        mesh = Mesh(box_triangles(0, 0, 0, 1, 1, 1))
        loops = plane_slice(mesh, 0.5)
        self.assertEqual(len(loops), 1)
        self.assertTrue({(0, 0), (1, 0), (1, 1), (0, 1)}.issubset(loop_point_set(loops[0])))
        self.assertAlmostEqual(polygon_area(loops[0]), 1.0)

    def test_two_disjoint_boxes(self):
        triangles = box_triangles(0, 0, 0, 1, 1, 1) + box_triangles(10, 10, 0, 11, 11, 1)
        mesh = Mesh(triangles)
        loops = plane_slice(mesh, 0.5)
        self.assertEqual(len(loops), 2)
        point_sets = [loop_point_set(loop) for loop in loops]
        self.assertTrue(any({(0, 0), (1, 0), (1, 1), (0, 1)}.issubset(s) for s in point_sets))
        self.assertTrue(any({(10, 10), (11, 10), (11, 11), (10, 11)}.issubset(s) for s in point_sets))
        for loop in loops:
            self.assertAlmostEqual(polygon_area(loop), 1.0)

    def test_plane_outside_bbox_yields_no_loops(self):
        mesh = Mesh(box_triangles(0, 0, 0, 1, 1, 1))
        loops = plane_slice(mesh, 5.0)
        self.assertEqual(loops, [])


if __name__ == "__main__":
    unittest.main()
