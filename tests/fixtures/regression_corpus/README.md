# Real-world regression corpus

Every bug found in this project so far was caught by trying a *new*
real-world STL, never by the synthetic OpenSCAD-generated fixtures —
each fixture was added retroactively, after the fact. Synthetic
fixtures encode axes of variation we already thought of; real files
keep surfacing ones we didn't. This directory is where those files live
on so the bugs they found stay fixed.

## The policy

**Whenever a real-world file causes a bug, drop the file in this
directory and add an entry to `manifest.json`.** This is not optional —
it's the actual point of this corpus. A bug fix without a corpus entry
means the next regression on that exact file goes uncaught again.

## Why the STLs aren't committed to git

Files people share here are often downloaded third-party designs of
unclear license/redistribution rights (see the project's `.gitignore`,
which excludes all `*.stl`). So this directory is **local-only and
gitignored** — but `manifest.json` (metadata, no geometry) and this
README *are* committed, so the intent and expected behavior survive
even on a machine that doesn't have the actual files.

`tests/run_regression_corpus.py` reads the manifest and, for each
entry, runs the file through `gfbadjust` and checks it against
`tests/invariants.py` if the file is present locally; if it's missing,
it prints a note and skips that entry without failing. This means
`./tests/test_end_to_end.sh` is always safe to run on a fresh clone
(nothing here is required), but running it on the machine that
accumulated these files gets full regression coverage.

## Adding an entry

1. Copy the file into this directory.
2. Add an entry to `manifest.json`:
   ```json
   {
     "file": "some-bin.stl",
     "expected_feet": 32,
     "cli_args": [],
     "regression_for": "one-line description + commit hash of the fix",
     "note": "anything about the file's shape that made it tricky"
   }
   ```
3. `expected_feet` = (number of occupied 42mm cells) × 4. Get it from a
   known-good run's `-v` output (the "occupied cells (N/M)" line) after
   you've confirmed the fix is correct — don't guess.
4. Run `python3 tests/run_regression_corpus.py` to confirm it passes.
