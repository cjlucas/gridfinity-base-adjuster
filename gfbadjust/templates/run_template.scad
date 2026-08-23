// Static driver: cuts the original body at cut_z and reattaches a
// freshly generated base of independent 21mm feet under the cells
// listed in data.scad.
//
// data.scad and gridfinity_base.scad must sit alongside this file --
// OpenSCAD's include/use paths are resolved relative to it.

include <data.scad>
include <gridfinity_base.scad>

$fn = 32;

CELL_SIZE = 21;

module new_base() {
    for (c = occupied_cells) {
        translate([
            grid_origin[0] + c[0] * CELL_SIZE + CELL_SIZE / 2,
            grid_origin[1] + c[1] * CELL_SIZE + CELL_SIZE / 2,
            cut_z - BASE_HEIGHT
        ])
            sub_foot(CELL_SIZE);
    }
}

module body() {
    difference() {
        import(input_stl);
        translate([-1000, -1000, cut_z - 2000])
            cube([2000, 2000, 2000]);
    }
}

union() {
    body();
    new_base();
}
