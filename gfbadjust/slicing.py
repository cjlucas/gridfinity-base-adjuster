"""Plane-slice a triangle mesh into closed 2D polygon loops.

Standard "marching triangles" approach: find triangles straddling the
target Z plane, interpolate the crossing edges into 2D segments, then
chain segments into closed loops via shared endpoints. Works uniformly
for rectangular bins, L-shaped bins, and (in general) meshes with holes
or multiple disjoint footprint islands -- no special-casing needed, the
even-odd fill rule in geometry.point_in_polygon handles those downstream.
"""

from .geometry import edge_plane_intersection


def plane_slice(mesh, z):
    segments = []
    for triangle in mesh.triangles:
        points = []
        for i in range(3):
            a = triangle[i]
            b = triangle[(i + 1) % 3]
            za = a[2] - z
            zb = b[2] - z
            if za == 0.0:
                points.append((a[0], a[1]))
            if za * zb < 0.0:
                points.append(edge_plane_intersection(a, b, z))
        if len(points) == 2:
            segments.append((points[0], points[1]))
    return _chain_segments(segments)


def _chain_segments(segments, precision=5):
    def snap(pt):
        return (round(pt[0], precision), round(pt[1], precision))

    point_coords = {}
    edges = []
    for (p, q) in segments:
        kp, kq = snap(p), snap(q)
        if kp == kq:
            continue  # degenerate zero-length segment
        point_coords.setdefault(kp, p)
        point_coords.setdefault(kq, q)
        edges.append((kp, kq))

    incident = {}
    for idx, (kp, kq) in enumerate(edges):
        incident.setdefault(kp, []).append(idx)
        incident.setdefault(kq, []).append(idx)

    used = [False] * len(edges)
    loops = []
    for start_idx in range(len(edges)):
        if used[start_idx]:
            continue
        kp, kq = edges[start_idx]
        used[start_idx] = True
        start_key = kp
        loop_keys = [kp]
        current = kq
        while current != start_key:
            loop_keys.append(current)
            next_edge = None
            for e in incident.get(current, []):
                if not used[e]:
                    next_edge = e
                    break
            if next_edge is None:
                # open chain -- shouldn't happen against a watertight mesh
                break
            used[next_edge] = True
            a, b = edges[next_edge]
            current = b if a == current else a
        if len(loop_keys) >= 3:
            loops.append([point_coords[k] for k in loop_keys])
    return loops
