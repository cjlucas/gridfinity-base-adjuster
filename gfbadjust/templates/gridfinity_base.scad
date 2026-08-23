// Minimal, from-scratch Gridfinity base foot module.
//
// Dimensions reverse-engineered directly from real reference bins
// (gf-rebuilt "Standard" bins) since they're the ground truth: the
// chamfer profile (0.8mm chamfer, 1.8mm plateau, 2.15mm chamfer;
// 3.75mm corner radius; 4.75mm total height) is the SAME absolute
// geometry regardless of foot size -- a 21mm foot uses an identical
// profile to a 42mm foot, just applied around a smaller top island
// (cell_size - BASE_GAP_MM instead of 42 - BASE_GAP_MM). No magnet/
// screw holes, no lid/label geometry -- just the foot.

BASE_GAP_MM = 0.5;

// (inset, height) pairs, with height measured DOWNWARD from the top of
// the profile (where it meets the body, inset=0) to the bottom tip
// (inset=2.95, the narrowest point that noses into the baseplate).
BASE_PROFILE = [[0, 0], [2.15, 2.15], [2.15, 3.95], [2.95, 4.75]];

BASE_PROFILE_HEIGHT = 4.75;
BASE_HEIGHT = 4.75;

BASE_TOP_RADIUS = 3.75;

// A rounded square eroded by `inset` from a top_size/BASE_TOP_RADIUS
// square. Uniform offsetting a rounded rect inward by `d` shrinks its
// side by 2d and its corner radius by d -- this is what makes stacking
// these slabs and hull()-ing between consecutive ones reproduce the
// profile's chamfers exactly (the profile is a piecewise-linear,
// self-similar offset curve).
module _eroded_square(top_size, inset) {
    w = top_size - 2 * inset;
    r = max(0, BASE_TOP_RADIUS - inset);
    if (r < 0.001) {
        square([w, w], center = true);
    } else {
        offset(r = r) square([w - 2 * r, w - 2 * r], center = true);
    }
}

module _foot_slab(top_size, inset, height, thickness = 0.001) {
    // Flip the profile's top-down height into local Z measured from the
    // true bottom tip (local Z=0) upward, so the wide (inset=0) end
    // lands at BASE_PROFILE_HEIGHT, flush against the body above it.
    z = BASE_PROFILE_HEIGHT - height;
    translate([0, 0, z])
        linear_extrude(height = thickness)
            _eroded_square(top_size, inset);
}

// A single, fully independent Gridfinity-style foot sized to `cell_size`
// (e.g. 42 for a standard foot, 21 for a quarter-size one) -- same
// absolute BASE_PROFILE/BASE_TOP_RADIUS either way, just applied to a
// top island of (cell_size - BASE_GAP_MM) instead of always 41.5.
// Centered at local (0,0) in XY; spans local Z=0 (bottom tip) to
// Z=BASE_HEIGHT (top, meant to sit flush against the body's bottom
// face).
module sub_foot(cell_size) {
    top_size = cell_size - BASE_GAP_MM;
    for (i = [0 : len(BASE_PROFILE) - 2]) {
        p0 = BASE_PROFILE[i];
        p1 = BASE_PROFILE[i + 1];
        hull() {
            _foot_slab(top_size, p0[0], p0[1]);
            _foot_slab(top_size, p1[0], p1[1]);
        }
    }
}
