# gridfinity-base-adjuster

Takes an STL of a Gridfinity bin (or any Gridfinity-based item with a
standard, whole-cell footprint) and replaces its base with one built from
independent 21mm feet instead of standard 42mm feet — four feet per
original 42mm cell, each a fully self-contained foot using the real,
unscaled Gridfinity chamfer profile (not a scaled-down miniature).

Splitting every cell into a 2x2 grid of 21mm feet gives finer placement
granularity on the baseplate while staying dimensionally faithful to the
real spec — the chamfer, corner radius, and overall base height are
byte-for-byte the same geometry a standard 42mm foot uses, just applied
around a smaller top island.

The foot geometry and profile dimensions were reverse-engineered and
numerically verified against real reference bins (matched point-for-point
against a "gf-rebuilt" style Standard bin's actual mesh).

## Requirements

- Python 3 (stdlib only — no dependencies to install)
- [OpenSCAD](https://openscad.org/) available on `PATH` (or pass
  `--openscad-bin`)

## Usage

```
python3 -m gfbadjust INPUT.stl -o OUTPUT.stl [options]
```

Options:

| Flag | Default | Description |
| --- | --- | --- |
| `--base-height MM` | `4.75` | Expected height of the *existing* base to cut off. Adjust if your input uses a different base height. |
| `--grid-origin X,Y` | auto-detected | Manual override for the 42mm grid origin, skips auto-detection. |
| `--footprint-height MM` | `0.2` | Height above the cut plane to slice the footprint at. |
| `--openscad-bin PATH` | search `PATH` | Path to the `openscad` binary. |
| `--keep-intermediate` | off | Keep the generated `.scad`/data files instead of deleting the temp dir. |
| `--dry-run` | off | Run analysis and emit the generated `.scad` files only, skip invoking OpenSCAD. |
| `-v`, `--verbose` | off | Print the detected bbox, grid origin, and an ASCII dump of the occupied-cell grid. |

Example:

```
python3 -m gfbadjust my-2x2-bin.stl -o my-2x2-bin-21mm.stl -v
```

## How it works

1. Parse the input STL (a small hand-rolled binary/ASCII reader — no
   external mesh library needed).
2. Cut the model at `min_z + --base-height`, discarding everything below
   (the existing base).
3. Slice the kept body just above the cut plane to get its 2D footprint.
4. Snap that footprint's bounding box to the nearest 42mm grid and
   determine which 42mm cells it occupies (the input is assumed to be a
   whole number of full 42mm cells — no partial-cell footprints).
5. Generate a fresh base: every occupied 42mm cell becomes 4 independent
   21mm feet, each built from the real Gridfinity chamfer profile
   applied to a `21mm - gap` top island.
6. Hand the cut body plus the newly generated base to OpenSCAD, which
   does the actual boolean union/render into the output STL.

All of the actual solid modeling (the cut and the final union) is done by
OpenSCAD's CGAL-backed boolean engine — the Python side only measures the
input and writes out the parameters OpenSCAD needs.

## Assumptions / limitations

- The input's footprint must be a whole number of full 42mm Gridfinity
  cells (no partial-cell/irregular footprints in this version).
- The input mesh should be in millimeters and reasonably watertight.
- No magnet/screw holes are generated in the new base.

## Testing

```
python3 -m unittest discover -s tests
./tests/test_end_to_end.sh
```

The end-to-end test builds several synthetic fixtures with OpenSCAD
(plain rectangular, L-shaped, positioned far from world origin, and
built from disconnected per-cell blocks) and checks the tool's output
against each with `tests/check_output.py` — a set of reusable
correctness invariants (see `tests/invariants.py`) rather than exact
geometry matches. It also runs a local real-world regression corpus if
one is present (see `tests/fixtures/regression_corpus/README.md`) — see
`CLAUDE.md` for the full testing strategy and why that corpus matters.
