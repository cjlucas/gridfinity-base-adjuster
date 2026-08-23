#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OPENSCAD="${OPENSCAD_BIN:-openscad}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "== building fixtures =="
"$OPENSCAD" -D 'fixture="rect"' -o "$WORK_DIR/simple_bin.stl" tests/fixtures/make_fixtures.scad
"$OPENSCAD" -D 'fixture="lshape"' -o "$WORK_DIR/lshape_bin.stl" tests/fixtures/make_fixtures.scad

echo "== running gfbadjust on simple_bin =="
python3 -m gfbadjust "$WORK_DIR/simple_bin.stl" -o "$WORK_DIR/simple_out.stl" -v

echo "== running gfbadjust on lshape_bin =="
python3 -m gfbadjust "$WORK_DIR/lshape_bin.stl" -o "$WORK_DIR/lshape_out.stl" -v

echo "== sanity-checking outputs =="
python3 - "$WORK_DIR/simple_out.stl" "$WORK_DIR/lshape_out.stl" <<'EOF'
import sys
from gfbadjust import stl_io

for path in sys.argv[1:]:
    mesh = stl_io.load_stl(path)
    (min_x, min_y, min_z), (max_x, max_y, max_z) = mesh.bbox()
    assert len(mesh.triangles) > 0, f"{path}: no triangles"
    assert max_z - min_z > 7.0, f"{path}: suspiciously short bbox"
    print(f"{path}: OK ({len(mesh.triangles)} triangles, bbox height {max_z - min_z:.2f}mm)")
EOF

echo "== all checks passed =="
