// Static driver: cuts everything above lip_cut_z off the imported body.
// data.scad must sit alongside this file -- OpenSCAD's include paths
// are resolved relative to it.
//
// Unlike gfbadjust's run_template.scad, there's no rebuild step here --
// lip removal is a plain flat-plane cut, nothing gets added back.

include <data.scad>

$fn = 32;

// Clipping box sized around the input's own XY bbox (with a generous
// margin), not a fixed box around world origin -- see gfbadjust's
// CLAUDE.md gotcha this mirrors: a model can sit anywhere in its own
// file's coordinate space, and a hardcoded box risks clipping nothing
// at all if the model happens to sit outside it.
CLIP_MARGIN = 1000;

module body() {
    bbox_min = input_xy_bbox[0];
    bbox_max = input_xy_bbox[1];
    difference() {
        import(input_stl);
        translate([
            bbox_min[0] - CLIP_MARGIN,
            bbox_min[1] - CLIP_MARGIN,
            lip_cut_z
        ])
            cube([
                (bbox_max[0] - bbox_min[0]) + 2 * CLIP_MARGIN,
                (bbox_max[1] - bbox_min[1]) + 2 * CLIP_MARGIN,
                2000
            ]);
    }
}

body();
