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
"$OPENSCAD" -D 'fixture="islands"' -o "$WORK_DIR/islands_bin.stl" tests/fixtures/make_fixtures.scad

run_and_check() {
    local name="$1" expected_feet="$2"
    echo "== $name (expect $expected_feet feet) =="
    python3 -m gfbadjust "$WORK_DIR/$name.stl" -o "$WORK_DIR/${name}_out.stl" -v
    python3 tests/check_output.py "$WORK_DIR/$name.stl" "$WORK_DIR/${name}_out.stl" --expected-feet "$expected_feet"
}

run_and_check simple_bin 24
run_and_check lshape_bin 12
run_and_check offset_bin 24
run_and_check islands_bin 24

echo "== running the real-world regression corpus (if any files are present) =="
python3 tests/run_regression_corpus.py

echo "== all checks passed =="
