# Real-world regression corpus (gfladjust / stacking lip)

Mirrors `tests/fixtures/regression_corpus/`'s policy, for `gfladjust`
(the stacking-lip remover) instead of `gfbadjust` (the base replacer) --
see that directory's README for the full rationale. Short version: every
bug in this project has been found via a new real-world file, never a
synthetic fixture someone thought of in advance, so any real file that
finds one belongs here permanently.

## Why the STLs aren't committed to git

Same reason as the other corpus: third-party files of unclear
redistribution rights. This directory is **local-only and gitignored**
(`*.stl` in the root `.gitignore`) -- `manifest.json` and this README
are committed so intent/expected behavior survive even without the
files present.

`tests/run_lip_regression_corpus.py` reads the manifest and, for each
entry present locally, runs it through `gfladjust` and checks the
result against `tests/lip_invariants.py`; missing files are skipped
with a note rather than failed, so `./tests/test_lip_end_to_end.sh` is
always safe on a fresh clone.

## Adding an entry

1. Copy the file into this directory.
2. Add an entry to `manifest.json`:
   ```json
   {
     "file": "some-bin.stl",
     "expected_lip_height": 3.55,
     "regression_for": "one-line description + commit hash of the fix",
     "note": "anything about the file's shape that made it tricky"
   }
   ```
   Use `"expect_no_lip": true` instead of `expected_lip_height` for a
   file that should be correctly detected as having no lip at all
   (`gfladjust` should exit with its "nothing to remove" error).
3. Get `expected_lip_height` from a known-good `-v` run's "detected
   stacking lip: N mm" line after confirming the detection is correct
   by other means (e.g. comparing against a known lip-less twin of the
   same file, as the two files already here do) -- don't guess.
4. Run `python3 tests/run_lip_regression_corpus.py` to confirm it passes.
