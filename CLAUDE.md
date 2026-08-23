# CLAUDE.md

Guidance for Claude Code (or any future agent) working in this repo.

## What this is

`gfbadjust` takes an STL of a Gridfinity bin/holder and replaces its base:
every existing 42mm cell becomes 4 independent 21mm feet instead of one
42mm foot. Each 21mm foot is a fully self-contained foot using the real,
unscaled Gridfinity chamfer profile — not a scaled-down miniature, and
not a trimmed quarter of a bigger foot. See `README.md` for user-facing
usage.

## Architecture: Python measures, OpenSCAD builds

Python (`gfbadjust/*.py`, stdlib only, no dependencies) does analysis
only: parse the STL, find the cut plane, slice the footprint, detect the
grid, rasterize occupied cells. It writes those results into a generated
`data.scad` and hands off to `gfbadjust/templates/run_template.scad`,
which `import()`s the original STL and does the actual cut + rebuild via
OpenSCAD's CGAL boolean engine (`gfbadjust/cli.py` shells out to
`openscad`). Don't reach for a Python mesh-boolean library (trimesh,
manifold3d, etc.) here — the OpenSCAD split was a deliberate choice
because OpenSCAD is a robust, already-available CSG engine, and it keeps
Python dependency-free.

Key modules:
- `stl_io.py` — hand-rolled binary/ASCII STL reader (triangle soup, no
  vertex dedup needed for our purposes).
- `slicing.py` — plane-slices the mesh into closed 2D polygon loops via
  "marching triangles" + loop-chaining. Handles holes/multiple islands
  naturally via the even-odd fill rule in `geometry.point_in_polygon`.
- `gridfit.py` — derives the 42mm grid origin from the footprint's bbox.
- `rasterize.py` — determines which cells are occupied via centroid
  point-in-polygon tests.
- `templates/gridfinity_base.scad` — the actual foot geometry
  (`sub_foot(cell_size)`), parameterized so the same profile works at
  42mm or 21mm.
- `templates/run_template.scad` — static driver: cuts the body, places a
  `sub_foot(21)` at every occupied cell, unions it all together.

## Hard-won gotchas (don't reintroduce these)

**`BASE_PROFILE` height direction is easy to get backwards.** The
profile in `constants.py`/`gridfinity_base.scad` is stored as
`(inset, height)` pairs with height measured *downward from the top* of
the foot (where it meets the body, inset=0) to the bottom tip
(inset=2.95, height=4.75). It's tempting to also swap which chamfer
segment (0.8mm vs 2.15mm) gets which inset value when converting — get
this wrong and you silently get a plausible-looking but wrong taper
direction or wrong plateau width. The current values were reverse
engineered and numerically verified against real reference bins (see
"Verifying geometry changes" below) — don't hand-edit them without
re-verifying the same way.

**Grid origin must NOT be snapped to a global multiple of 42mm from
world (0,0).** An earlier version did `round(bbox_min / 42) * 42`, which
only worked by coincidence on files whose footprint happened to sit near
a clean multiple. A hand-placed custom holder can sit at any arbitrary
offset in its own file; snapping to the nearest global multiple silently
picks the wrong cell boundary and shifts the entire generated base by
however far off that rounding was (was observed as a multi-mm overhang
in practice). `gridfit.compute_grid_origin` now derives the origin
directly from the footprint's own bbox corner (with the known half-gap
correction) — never from an external frame.

**Loop-based measurements (grid origin, extent) must use the *main*
loop, not all loops pooled together.** A footprint slice can pick up
small internal features (holes, divider walls, slots) as extra small
loops. Pooling every point across every loop into a single bbox lets
those features skew origin/extent detection. Use
`geometry.main_loop()` (largest-bbox-area loop) for measurements, and
only fall back to testing against *all* loops for the actual
point-in-polygon occupancy check (where holes need to be respected).

**The multi-loop warning in `cli.py` only fires for *large* secondary
loops** (≥20% of the main loop's area), not any extra loop — small
loops from a holder's internal dividers are completely normal and not a
sign of a bad `--base-height`. A real bad-height symptom looks like a
large nested loop close in size to the main outline (sliced into the
hollow interior), not tiny internal features.

**`--base-height` default is 4.75mm, not the reference implementation's
7mm.** An earlier iteration conflated an OpenSCAD reference project's
own "profile + bridge = one Z-unit" convention (7mm) with the actual
base height most real-world Gridfinity STLs use. 4.75mm was confirmed
against two independent real-world files. `--base-height` remains
user-overridable since generators do vary.

**The cut's clipping box in `run_template.scad` must never be hardcoded
around world origin.** It was originally a fixed `[-1000,1000]` box in
X/Y; any model positioned outside that range (e.g. a part laid out far
from origin on a build plate — one real file had X coordinates around
1400) meant the clip silently intersected nothing, so `difference()`
removed no material at all. The original base survived completely
intact, fused underneath the newly added feet, producing the confusing
symptom of the *old* 42mm feet still being visibly present in the
output. The clip box is now sized from the input's own XY bbox (passed
through via `data.scad`) plus a margin — always derive spatial extents
from the actual model, never assume it's near any particular absolute
coordinate. `tests/fixtures/make_fixtures.scad`'s `"offset"` fixture
(positioned far from origin) is a regression test for exactly this.

## Scope / assumptions

- Input footprint must be a whole number of full 42mm cells — no
  partial-cell/irregular footprints in this version. This was a
  deliberate scope decision, not a limitation to silently work around.
- No magnet/screw holes are generated in the new base.
- Input mesh assumed to be in millimeters and reasonably watertight.

## Commands

```
python3 -m unittest discover -s tests   # unit tests, no OpenSCAD needed
./tests/test_end_to_end.sh              # builds fixtures + runs the CLI, needs openscad on PATH
python3 -m gfbadjust INPUT.stl -o OUTPUT.stl -v
```

## Verifying geometry changes

If you touch anything in `templates/gridfinity_base.scad` or the profile
constants, don't just eyeball a render — verify numerically. The
pattern used throughout this project's history: slice the mesh at many
Z heights (`slicing.plane_slice`), track the loop width at each height
to reconstruct the actual (inset, height) curve, and compare it point-
for-point against a known-good reference bin if one is available. A
quick visual render (`openscad --camera=... -o preview.png`, viewed with
the Read tool) is a good sanity check but has repeatedly missed subtle
directional/magnitude bugs that numeric comparison caught immediately.
