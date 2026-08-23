#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OPENSCAD="${OPENSCAD_BIN:-openscad}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "== building fixtures =="
"$OPENSCAD" -D 'fixture="rect"' -o "$WORK_DIR/simple_bin.stl" tests/fixtures/make_fixtures.scad
"$OPENSCAD" -D 'fixture="lshape"' -o "$WORK_DIR/lshape_bin.stl" tests/fixtures/make_fixtures.scad
"$OPENSCAD" -D 'fixture="offset"' -o "$WORK_DIR/offset_bin.stl" tests/fixtures/make_fixtures.scad

echo "== running gfbadjust on simple_bin =="
python3 -m gfbadjust "$WORK_DIR/simple_bin.stl" -o "$WORK_DIR/simple_out.stl" -v

echo "== running gfbadjust on lshape_bin =="
python3 -m gfbadjust "$WORK_DIR/lshape_bin.stl" -o "$WORK_DIR/lshape_out.stl" -v

echo "== running gfbadjust on offset_bin (far from world origin) =="
python3 -m gfbadjust "$WORK_DIR/offset_bin.stl" -o "$WORK_DIR/offset_out.stl" -v

echo "== sanity-checking outputs =="
python3 - "$WORK_DIR/simple_out.stl" "$WORK_DIR/lshape_out.stl" "$WORK_DIR/offset_out.stl" <<'EOF'
import sys
from gfbadjust import stl_io, slicing
from gfbadjust.geometry import loop_bbox

for path in sys.argv[1:]:
    mesh = stl_io.load_stl(path)
    (min_x, min_y, min_z), (max_x, max_y, max_z) = mesh.bbox()
    assert len(mesh.triangles) > 0, f"{path}: no triangles"
    assert max_z - min_z > 7.0, f"{path}: suspiciously short bbox"

    # Regression check: near the very bottom, every foot must be ~21mm
    # scale, not the original ~35-41mm 42mm-foot scale -- catches the
    # "old base survived because the cut clipped nothing" bug class.
    loops = slicing.plane_slice(mesh, min_z + 0.5)
    assert loops, f"{path}: no loops found near the bottom"
    max_foot_size = max(loop_bbox(l)[2] - loop_bbox(l)[0] for l in loops)
    assert max_foot_size < 25.0, (
        f"{path}: found a foot {max_foot_size:.1f}mm wide near the bottom -- "
        "looks like an old 42mm foot survived the cut"
    )

    print(f"{path}: OK ({len(mesh.triangles)} triangles, bbox height {max_z - min_z:.2f}mm, "
          f"max foot width near bottom {max_foot_size:.1f}mm)")
EOF

echo "== all checks passed =="
