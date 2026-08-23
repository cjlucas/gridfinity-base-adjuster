"""Small 2D/3D geometry helpers."""


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
