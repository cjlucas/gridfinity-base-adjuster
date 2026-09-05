// Synthetic test bins for gfladjust's stacking-lip auto-detection.
// Select which fixture to render with:
//   openscad -D 'fixture="with_lip"'     -o with_lip.stl make_lip_fixtures.scad
//   openscad -D 'fixture="no_lip"'       -o no_lip.stl make_lip_fixtures.scad
//   openscad -D 'fixture="coincidental"' -o coincidental.stl make_lip_fixtures.scad
//   openscad -D 'fixture="inner_lip"'    -o inner_lip.stl make_lip_fixtures.scad
//
// These don't reproduce the real Gridfinity lip profile (see
// gfladjust/lip_detect.py's module docstring for the real mechanism --
// an inner-bore shelf, reverse engineered from gridfinity-rebuilt
// -openscad's own source). They only need to exercise the actual
// detector logic: total height modulo the 7mm unit, confirmed by an
// outer-footprint OR inner-bore change near the top.

$fn = 32;

UNIT_HEIGHT = 7;
UNITS = 6;
WALL_HEIGHT = UNITS * UNIT_HEIGHT; // 42
SIZE = 40;

LIP_HEIGHT = 3.6; // within lip_detect's [2.5, 5.0]mm plausible band
LIP_INSET = 1.0;  // outer footprint shrinks by this much (per side) at the top

module plain_box(height) {
    cube([SIZE, SIZE, height], center = false);
}

// A plain box topped with a smaller box -- stands in for a real lip's
// outer-footprint dip near the tip.
module box_with_lip() {
    union() {
        plain_box(WALL_HEIGHT);
        translate([LIP_INSET, LIP_INSET, WALL_HEIGHT])
            cube([SIZE - 2 * LIP_INSET, SIZE - 2 * LIP_INSET, LIP_HEIGHT]);
    }
}

// Same total height as box_with_lip (WALL_HEIGHT + LIP_HEIGHT), but
// flat the entire way -- a legitimate object that happens to land
// within the plausible lip-height remainder band without actually
// having a lip. Regression test for the confirmation check refusing to
// guess rather than mis-cutting a real object.
module box_coincidental_height() {
    plain_box(WALL_HEIGHT + LIP_HEIGHT);
}

// Hollow box whose OUTER footprint never changes at all -- only the
// inner cavity narrows (thicker "wall") for the top LIP_HEIGHT mm.
// Regression fixture for a real bug: a real-world "Field Notes holder"
// bin's lip only shows up in its inner bore, not its outer wall, and an
// outer-only confirmation check missed it entirely (see
// tests/fixtures/lip_regression_corpus/).
WALL_THICK = 2;
LIP_WALL_THICK = 12;
FLOOR = 5;

module hollow_box_with_inner_lip() {
    total_height = WALL_HEIGHT + LIP_HEIGHT;
    difference() {
        cube([SIZE, SIZE, total_height]);
        translate([WALL_THICK, WALL_THICK, FLOOR])
            cube([SIZE - 2 * WALL_THICK, SIZE - 2 * WALL_THICK, WALL_HEIGHT - FLOOR + 0.01]);
        translate([LIP_WALL_THICK, LIP_WALL_THICK, WALL_HEIGHT - 0.01])
            cube([SIZE - 2 * LIP_WALL_THICK, SIZE - 2 * LIP_WALL_THICK, LIP_HEIGHT + 0.02]);
    }
}

fixture = "with_lip";

if (fixture == "no_lip") {
    plain_box(WALL_HEIGHT);
} else if (fixture == "coincidental") {
    box_coincidental_height();
} else if (fixture == "inner_lip") {
    hollow_box_with_inner_lip();
} else {
    box_with_lip();
}
