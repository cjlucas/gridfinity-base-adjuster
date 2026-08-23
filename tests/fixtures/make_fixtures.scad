// Builds synthetic test bins using the same sub_foot() module the tool
// itself uses, so the fixtures' original feet are a known-correct
// reference (standard 42mm feet, since the input is assumed to always
// be whole-cell). Select which fixture to render with:
//   openscad -D 'fixture="rect"'   -o simple_bin.stl make_fixtures.scad
//   openscad -D 'fixture="lshape"' -o lshape_bin.stl make_fixtures.scad

include <../../gfbadjust/templates/gridfinity_base.scad>

$fn = 32;

WALL_HEIGHT = 25;

RECT_CELLS = [[0, 0], [1, 0], [0, 1], [1, 1], [0, 2], [1, 2]]; // 2x3
LSHAPE_CELLS = [[0, 0], [1, 0], [0, 1]]; // 2x2 missing [1,1]

fixture = "rect";

module fixture_bin(cells) {
    union() {
        for (c = cells)
            translate([c[0] * 42 + 21, c[1] * 42 + 21, 0])
                sub_foot(42);
        for (c = cells)
            translate([c[0] * 42, c[1] * 42, BASE_HEIGHT])
                cube([42, 42, WALL_HEIGHT]);
    }
}

cells = (fixture == "lshape") ? LSHAPE_CELLS : RECT_CELLS;
fixture_bin(cells);
