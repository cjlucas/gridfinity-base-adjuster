#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

OPENSCAD="${OPENSCAD_BIN:-openscad}"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

echo "== building fixtures =="
"$OPENSCAD" -D 'fixture="with_lip"'     -o "$WORK_DIR/with_lip.stl"     tests/fixtures/make_lip_fixtures.scad
"$OPENSCAD" -D 'fixture="no_lip"'       -o "$WORK_DIR/no_lip.stl"       tests/fixtures/make_lip_fixtures.scad
"$OPENSCAD" -D 'fixture="coincidental"' -o "$WORK_DIR/coincidental.stl" tests/fixtures/make_lip_fixtures.scad
"$OPENSCAD" -D 'fixture="inner_lip"'    -o "$WORK_DIR/inner_lip.stl"    tests/fixtures/make_lip_fixtures.scad

echo "== with_lip (expect lip height 3.6mm) =="
python3 -m gfladjust "$WORK_DIR/with_lip.stl" -o "$WORK_DIR/with_lip_out.stl" -v
python3 tests/check_lip_output.py "$WORK_DIR/with_lip.stl" "$WORK_DIR/with_lip_out.stl" --expected-lip-height 3.6

echo "== no_lip (expect a clean 'nothing to remove' error) =="
if python3 -m gfladjust "$WORK_DIR/no_lip.stl" -o "$WORK_DIR/no_lip_out.stl" -v; then
    echo "FAIL: expected gfladjust to report no lip detected, but it succeeded"
    exit 1
fi
echo "OK   correctly reported no lip detected"

echo "== coincidental (same height remainder as with_lip, but no real lip -- expect a refusal) =="
if python3 -m gfladjust "$WORK_DIR/coincidental.stl" -o "$WORK_DIR/coincidental_out.stl" -v; then
    echo "FAIL: expected gfladjust to refuse a coincidentally unit-aligned height, but it succeeded"
    exit 1
fi
echo "OK   correctly refused to guess"

echo "== inner_lip (lip only visible in the inner bore, expect lip height 3.6mm) =="
python3 -m gfladjust "$WORK_DIR/inner_lip.stl" -o "$WORK_DIR/inner_lip_out.stl" -v
python3 tests/check_lip_output.py "$WORK_DIR/inner_lip.stl" "$WORK_DIR/inner_lip_out.stl" --expected-lip-height 3.6

echo "== running the real-world lip regression corpus (if any files are present) =="
python3 tests/run_lip_regression_corpus.py

echo "== all lip checks passed =="
