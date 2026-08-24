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

**Loop-based measurements (grid origin, extent) must pool ALL loops,
not just the single largest one.** An earlier version measured extent
from only `geometry.main_loop()` (the largest-bbox-area loop), reasoning
that small internal features (holes, divider walls, slots) shouldn't be
able to skew the bbox. That's true, but it also silently assumed
there's always exactly one loop representing the whole footprint — false
for a bin built from several separate, similarly-sized physical blocks
with gaps between them (e.g. independent per-cell compartments): no
single loop there is "the" footprint, so picking the biggest one
truncated detection down to a single cell, and most of the bin got no
base at all. `gridfit.compute_grid_origin`/`rasterize.rasterize` now use
`geometry.all_loops_bbox` (pool every point of every loop). This is safe
for the original hole/divider case too: a hole is always strictly
inside the outer boundary, so pooling can't let it corrupt the bbox —
excluding it was never actually necessary. `geometry.main_loop()` still
exists, used only as an informal "biggest single chunk" reference for
the multi-loop sanity warning in `cli.py`, not for real measurements.

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
python3 -m unittest discover -s tests        # unit tests, no OpenSCAD needed
./tests/test_end_to_end.sh                   # synthetic fixtures + real-world corpus, needs openscad on PATH
python3 tests/check_output.py IN.stl OUT.stl --expected-feet N   # ad hoc invariant check on any pair
python3 -m gfbadjust INPUT.stl -o OUTPUT.stl -v
```

## Testing strategy

**The actual failure pattern in this project's history: every real bug
so far was found only when a new real-world STL was tried — never by
the synthetic fixtures, which were all added *after* the fact.**
Synthetic fixtures only encode variation axes someone already thought
of; real files keep surfacing ones nobody did (a footprint positioned
far from world origin, a bin built from disconnected per-cell blocks,
etc.). The testing setup here is layered specifically around that
pattern, not just "add more unit tests":

1. **Unit tests** (`tests/test_*.py`, `python3 -m unittest discover -s
   tests`) — fast, no OpenSCAD, test pure Python logic (slicing,
   gridfit, rasterize) against small hand-built inputs. Good for
   pinning down a specific function's behavior once you know what
   matters; not designed to catch geometry-level integration issues.

2. **Invariant checks** (`tests/invariants.py`, driven by
   `tests/check_output.py`) — properties that must hold for *any* valid
   input/output pair, not exact-match assertions about one specific
   fixture's expected geometry: output isn't empty, no leftover
   42mm-scale feet, output XY bbox matches input XY bbox, foot count
   matches expectation. Each one exists because it's exactly the kind of
   check that would have caught a specific real regression (see the
   docstrings in `invariants.py` for which commit each one guards
   against). When you fix a new bug, ask first whether it's actually a
   *new class* of invariant (something no existing check would catch)
   before reaching for another fixture — a new invariant generalizes to
   files you haven't seen yet; a fixture only covers the one you have.

3. **Synthetic fixtures** (`tests/fixtures/make_fixtures.scad`, run via
   `tests/test_end_to_end.sh`) — deliberately span known-tricky axes,
   each one added because a real file hit it: `rect`/`lshape` (basic
   shapes), `offset` (positioned far from world origin), `islands`
   (built from disconnected per-cell blocks). When adding a new one,
   name it for the *property* it tests, not the file that found it, and
   wire an expected foot count into `test_end_to_end.sh`'s
   `run_and_check` calls.

4. **Real-world regression corpus**
   (`tests/fixtures/regression_corpus/`, run via
   `tests/run_regression_corpus.py`, wired into
   `test_end_to_end.sh`) — actual third-party files that broke the tool,
   kept permanently (gitignored locally, tracked via a committed
   `manifest.json` — see that directory's README for the policy and
   licensing reasoning). **This is the layer that has actually caught
   every bug so far, so it's the one that must never be skipped when
   fixing a new one.**

**The rule when fixing any bug found via a new file:** (a) add an
invariant to `invariants.py` if the failure represents a new class of
wrongness, (b) add or extend a synthetic fixture that reproduces the
specific structural property that broke it (not just the literal file),
(c) drop the actual file into the regression corpus with a manifest
entry, (d) document the gotcha in this file's list above. Steps (a)-(c)
are about *never regressing on this again, including on files you
haven't seen*; step (d) is about a future agent not reintroducing the
same wrong assumption from a different angle.

**Verifying geometry changes specifically:** if you touch anything in
`templates/gridfinity_base.scad` or the profile constants, don't just
eyeball a render — verify numerically. Slice the mesh at many Z heights
(`slicing.plane_slice`), track the loop width at each height to
reconstruct the actual (inset, height) curve, and compare it
point-for-point against a known-good reference bin if one is available.
A quick visual render (`openscad --camera=... -o preview.png`, viewed
with the Read tool) is a good sanity check but has repeatedly missed
subtle directional/magnitude bugs that numeric comparison caught
immediately.
