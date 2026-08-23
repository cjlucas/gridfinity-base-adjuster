"""Minimal STL reader (binary + ASCII), stdlib only.

Produces a flat triangle soup -- no vertex deduplication/indexing is
needed for bounding-box and plane-slicing purposes.
"""

import struct


class Mesh:
    def __init__(self, triangles):
        # triangles: list of ((x,y,z), (x,y,z), (x,y,z))
        self.triangles = triangles

    def bbox(self):
        xs = []
        ys = []
        zs = []
        for tri in self.triangles:
            for (x, y, z) in tri:
                xs.append(x)
                ys.append(y)
                zs.append(z)
        if not xs:
            raise ValueError("mesh has no triangles")
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def load_stl(path):
    with open(path, "rb") as f:
        data = f.read()

    if _looks_binary(data):
        return _parse_binary(data)
    return _parse_ascii(data.decode("ascii", errors="replace"))


def _looks_binary(data):
    if len(data) < 84:
        return False
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    expected_size = 84 + triangle_count * 50
    return expected_size == len(data)


def _parse_binary(data):
    triangle_count = struct.unpack_from("<I", data, 80)[0]
    triangles = []
    offset = 84
    for _ in range(triangle_count):
        # normal (3f), v1 (3f), v2 (3f), v3 (3f), attribute byte count (H)
        values = struct.unpack_from("<12fH", data, offset)
        v1 = values[3:6]
        v2 = values[6:9]
        v3 = values[9:12]
        triangles.append((v1, v2, v3))
        offset += 50
    return Mesh(triangles)


def _parse_ascii(text):
    triangles = []
    current_vertices = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("vertex"):
            parts = stripped.split()
            x, y, z = (float(parts[1]), float(parts[2]), float(parts[3]))
            current_vertices.append((x, y, z))
            if len(current_vertices) == 3:
                triangles.append(tuple(current_vertices))
                current_vertices = []
    return Mesh(triangles)
