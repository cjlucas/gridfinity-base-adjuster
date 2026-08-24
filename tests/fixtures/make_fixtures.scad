// Builds synthetic test bins using the same sub_foot() module the tool
// itself uses, so the fixtures' original feet are a known-correct
// reference (standard 42mm feet, since the input is assumed to always
// be whole-cell). Select which fixture to render with:
//   openscad -D 'fixture="rect"'      -o simple_bin.stl make_fixtures.scad
//   openscad -D 'fixture="lshape"'    -o lshape_bin.stl make_fixtures.scad
//   openscad -D 'fixture="offset"'    -o offset_bin.stl make_fixtures.scad
//   openscad -D 'fixture="islands"'   -o islands_bin.stl make_fixtures.scad

include <../../gfbadjust/templates/gridfinity_base.scad>

$fn = 32;

WALL_HEIGHT = 25;

RECT_CELLS = [[0, 0], [1, 0], [0, 1], [1, 1], [0, 2], [1, 2]]; // 2x3
LSHAPE_CELLS = [[0, 0], [1, 0], [0, 1]]; // 2x2 missing [1,1]

// Same layout as "rect", but positioned far from world (0,0) -- e.g. a
// part laid out far from the origin on a build plate. Regression test
// for a bug where the cut's clipping box was a fixed box around world
// origin and silently clipped nothing for models positioned outside it.
OFFSET_ORIGIN = [1400, 200];

fixture = "rect";

module fixture_bin(cells, origin = [0, 0]) {
    union() {
        for (c = cells)
            translate([origin[0] + c[0] * 42 + 21, origin[1] + c[1] * 42 + 21, 0])
                sub_foot(42);
        for (c = cells)
            translate([origin[0] + c[0] * 42, origin[1] + c[1] * 42, BASE_HEIGHT])
                cube([42, 42, WALL_HEIGHT]);
    }
}

// Same layout as "rect", but each cell is its OWN separate physical
// block (foot + wall), not fused into one continuous body -- walls are
// inset slightly so neighboring cells never touch. Regression test for
// a bug where footprint detection assumed a single "main" outer loop
// and silently truncated a multi-island footprint down to one cell.
ISLAND_WALL_INSET = 0.1;

module fixture_bin_islands(cells, origin = [0, 0]) {
    wall_size = 42 - 2 * ISLAND_WALL_INSET;
    union() {
        for (c = cells)
            translate([origin[0] + c[0] * 42 + 21, origin[1] + c[1] * 42 + 21, 0])
                sub_foot(42);
        for (c = cells)
            translate([
                origin[0] + c[0] * 42 + ISLAND_WALL_INSET,
                origin[1] + c[1] * 42 + ISLAND_WALL_INSET,
                BASE_HEIGHT
            ])
                cube([wall_size, wall_size, WALL_HEIGHT]);
    }
}

if (fixture == "lshape") {
    fixture_bin(LSHAPE_CELLS);
} else if (fixture == "offset") {
    fixture_bin(RECT_CELLS, OFFSET_ORIGIN);
} else if (fixture == "islands") {
    fixture_bin_islands(RECT_CELLS);
} else {
    fixture_bin(RECT_CELLS);
}
