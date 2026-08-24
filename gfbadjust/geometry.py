"""Small 2D/3D geometry helpers."""


def loop_bbox(loop):
    xs = [p[0] for p in loop]
    ys = [p[1] for p in loop]
    return min(xs), min(ys), max(xs), max(ys)


def main_loop(loops):
    """The loop enclosing the largest bbox area.

    Only meaningful as an informal "biggest single chunk" reference (e.g.
    for the multi-loop sanity warning in cli.py) -- NOT a safe way to get
    the true footprint's extent. A footprint can legitimately be made of
    several separate, similarly-sized loops (e.g. a holder built from
    independent per-cell blocks with gaps between them, none of which
    alone represents the whole footprint) with no single "main" one.
    """
    def bbox_area(loop):
        min_x, min_y, max_x, max_y = loop_bbox(loop)
        return (max_x - min_x) * (max_y - min_y)

    return max(loops, key=bbox_area)


def all_loops_bbox(loops):
    """Bbox across every point of every loop, pooled together.

    This is the correct way to measure a footprint's true extent: a hole
    or internal divider loop is always strictly inside the outer
    boundary so it can't corrupt the result, and a footprint made of
    several separate islands (see main_loop's docstring) is only
    measured correctly by including all of them.
    """
    xs = [p[0] for loop in loops for p in loop]
    ys = [p[1] for loop in loops for p in loop]
    return min(xs), min(ys), max(xs), max(ys)


def point_in_polygon(point, loops):
    """Even-odd point-in-polygon test against a set of closed 2D loops.

    Summing ray-crossings across every loop and checking the parity of
    the total implements the even-odd fill rule directly -- holes and
    disjoint islands fall out for free, no special-casing needed.
    """
    x, y = point
    crossings = 0
    for loop in loops:
        n = len(loop)
        for i in range(n):
            x1, y1 = loop[i]
            x2, y2 = loop[(i + 1) % n]
            if (y1 > y) != (y2 > y):
                x_at_y = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if x_at_y > x:
                    crossings += 1
    return crossings % 2 == 1


def lerp(a, b, t):
    return a + (b - a) * t


def edge_plane_intersection(p1, p2, z):
    """Interpolate the (x, y) point where segment p1-p2 crosses height z.

    Assumes p1.z and p2.z are on opposite sides of z (caller's job to check).
    """
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    t = (z - z1) / (z2 - z1)
    return (lerp(x1, x2, t), lerp(y1, y2, t))
