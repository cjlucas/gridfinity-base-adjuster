import struct
import unittest
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gfbadjust import stl_io


def make_binary_stl_bytes(triangles):
    header = b"\x00" * 80
    body = b""
    for (v1, v2, v3) in triangles:
        body += struct.pack("<12fH", 0.0, 0.0, 0.0, *v1, *v2, *v3, 0)
    return header + struct.pack("<I", len(triangles)) + body


def make_ascii_stl_text(triangles):
    lines = ["solid test"]
    for (v1, v2, v3) in triangles:
        lines.append("facet normal 0 0 0")
        lines.append("outer loop")
        for v in (v1, v2, v3):
            lines.append(f"vertex {v[0]} {v[1]} {v[2]}")
        lines.append("endloop")
        lines.append("endfacet")
    lines.append("endsolid test")
    return "\n".join(lines)


TRIANGLES = [
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 2.0)),
]


class TestStlIo(unittest.TestCase):
    def test_binary_roundtrip(self):
        data = make_binary_stl_bytes(TRIANGLES)
        with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as f:
            f.write(data)
            path = f.name
        mesh = stl_io.load_stl(path)
        self.assertEqual(len(mesh.triangles), 1)
        self.assertEqual(mesh.triangles[0], TRIANGLES[0])
        min_pt, max_pt = mesh.bbox()
        self.assertEqual(min_pt, (0.0, 0.0, 0.0))
        self.assertEqual(max_pt, (1.0, 1.0, 2.0))

    def test_ascii_roundtrip(self):
        text = make_ascii_stl_text(TRIANGLES)
        with tempfile.NamedTemporaryFile(suffix=".stl", mode="w", delete=False) as f:
            f.write(text)
            path = f.name
        mesh = stl_io.load_stl(path)
        self.assertEqual(len(mesh.triangles), 1)
        self.assertEqual(mesh.triangles[0], TRIANGLES[0])


if __name__ == "__main__":
    unittest.main()
