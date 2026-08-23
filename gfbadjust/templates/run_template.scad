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

// Clipping box sized around the input's own XY bbox (with a generous
// margin), not a fixed box around world origin -- a model can sit at
// any absolute position (e.g. laid out far from origin on a build
// plate), and a hardcoded ±1000mm box silently clips nothing at all if
// the model is positioned outside it.
CLIP_MARGIN = 1000;

module body() {
    bbox_min = input_xy_bbox[0];
    bbox_max = input_xy_bbox[1];
    difference() {
        import(input_stl);
        translate([
            bbox_min[0] - CLIP_MARGIN,
            bbox_min[1] - CLIP_MARGIN,
            cut_z - 2000
        ])
            cube([
                (bbox_max[0] - bbox_min[0]) + 2 * CLIP_MARGIN,
                (bbox_max[1] - bbox_min[1]) + 2 * CLIP_MARGIN,
                2000
            ]);
    }
}

union() {
    body();
    new_base();
}
