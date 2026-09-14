# gridfinity-base-adjuster

Two small command-line tools for adjusting a Gridfinity bin/holder STL:
`gfbadjust` replaces its base, and `gfladjust` removes its stacking lip.
Both are stdlib-only Python that hand off the actual cut/rebuild to
OpenSCAD.

## gfbadjust: replacing the base

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

### Requirements

- Python 3 (stdlib only — no dependencies to install)
- [OpenSCAD](https://openscad.org/) available on `PATH` (or pass
  `--openscad-bin`)

### Usage

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

### How it works

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

### Assumptions / limitations

- The input's footprint must be a whole number of full 42mm Gridfinity
  cells (no partial-cell/irregular footprints in this version).
- The input mesh should be in millimeters and reasonably watertight.
- No magnet/screw holes are generated in the new base.

## gfladjust: removing the stacking lip

Takes an STL of a Gridfinity bin that has a stacking lip (the raised rim
near the top of the walls that lets another bin nest on top of it) and
removes it, leaving a flush top edge.

The lip's height is **auto-detected**, not user-supplied — different
generators use slightly different lip heights/shapes, so a hardcoded
default risked silently cutting the wrong amount. Detection uses
Gridfinity's fixed 7mm height unit: a bin's base + walls always sum to a
whole multiple of it, and a lip is purely extra height added on top of
that, so `(total height) mod 7mm` gives a reliable candidate lip height,
confirmed by a quick check that the wall's outer profile actually
changes near the top. If a file's height doesn't look like a real lip,
the tool refuses to guess rather than risk cutting into legitimate
geometry. See `gfladjust/lip_detect.py` for the full reasoning.

### Requirements

Same as `gfbadjust` above (Python 3 stdlib-only, OpenSCAD on `PATH`).

### Usage

```
python3 -m gfladjust INPUT.stl -o OUTPUT.stl [options]
```

Options:

| Flag | Default | Description |
| --- | --- | --- |
| `--openscad-bin PATH` | search `PATH` | Path to the `openscad` binary. |
| `--keep-intermediate` | off | Keep the generated `.scad`/data files instead of deleting the temp dir. |
| `--dry-run` | off | Run detection and emit the generated `.scad` files only, skip invoking OpenSCAD. |
| `-v`, `--verbose` | off | Print the detected bbox and lip height. |

Example:

```
python3 -m gfladjust my-lipped-bin.stl -o my-lipped-bin-nolip.stl -v
```

If the input has no lip (its height is already a clean multiple of the
7mm unit), or the tool can't confidently confirm a real lip is present,
it exits with an error instead of modifying the file.

### Assumptions / limitations

- The input mesh should be in millimeters and reasonably watertight.
- Only removes a lip that runs around the entire top edge; a
  label-tab-style lip on one side only isn't detected (out of scope for
  now).
- No `--lip-height` override by design — see above.

## macOS Finder integration (Quick Actions)

On macOS, both tools are also available as Finder **Quick Actions** so
you can run them by right-clicking an STL without opening a terminal.

Install once:

```
./macos/install.sh
```

Then right-click one or more `.stl` files in Finder and choose:

- **Gridfinity: Adjust Base (21mm)** — runs `gfbadjust` with defaults,
  writes `<name>_21mm.stl` next to the input.
- **Gridfinity: Remove Stacking Lip** — runs `gfladjust` with defaults
  (auto-detected lip height), writes `<name>_nolip.stl` next to the
  input.

Both always run with the tools' default settings — use the CLI directly
if you need to override something like `--base-height`. A result is
overwritten if you run the same Quick Action again on the same file.

Success/failure is reported via a macOS notification. On failure, the
notification shows the error and the full log is kept under
`~/Library/Logs/GridfinityAdjuster/`. Non-STL files and folders in a
multi-selection are skipped rather than failing the whole batch.

If you move the repo to a different path, just re-run `./macos/install.sh`
to reinstall with the new path. To remove the Quick Actions, run
`./macos/uninstall.sh`.

## Testing

```
python3 -m unittest discover -s tests   # covers both tools
./tests/test_end_to_end.sh              # gfbadjust
./tests/test_lip_end_to_end.sh          # gfladjust
```

Each tool's end-to-end test builds synthetic fixtures with OpenSCAD and
checks the tool's output against reusable correctness invariants
(`tests/invariants.py` / `tests/lip_invariants.py`) rather than exact
geometry matches, then runs a local real-world regression corpus if one
is present (`tests/fixtures/regression_corpus/` /
`tests/fixtures/lip_regression_corpus/`) — see `CLAUDE.md` for the full
testing strategy and why that corpus matters.
