#!/usr/bin/env python3
"""Run gfbadjust + invariant checks against every file in the local
real-world regression corpus (tests/fixtures/regression_corpus/).

The corpus's STL files are gitignored (see that directory's README for
why) -- entries whose file isn't present locally are skipped with a
note, not failed, so this is always safe to run on a fresh clone.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

CORPUS_DIR = Path(__file__).parent / "fixtures" / "regression_corpus"
MANIFEST = CORPUS_DIR / "manifest.json"
CHECK_OUTPUT = Path(__file__).parent / "check_output.py"


def main():
    manifest = json.loads(MANIFEST.read_text())
    if not manifest:
        print("regression corpus manifest is empty")
        return 0

    ran = 0
    failed = 0
    for entry in manifest:
        input_path = CORPUS_DIR / entry["file"]
        if not input_path.exists():
            print(f"SKIP {entry['file']}: not present locally")
            continue

        ran += 1
        print(f"-- {entry['file']} ({entry.get('regression_for', 'no description')})")
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "output.stl"
            result = subprocess.run(
                [sys.executable, "-m", "gfbadjust", str(input_path), "-o", str(output_path)]
                + entry.get("cli_args", []),
                cwd=Path(__file__).parent.parent,
            )
            if result.returncode != 0:
                print(f"FAIL {entry['file']}: gfbadjust exited with {result.returncode}")
                failed += 1
                continue

            check_args = [sys.executable, str(CHECK_OUTPUT), str(input_path), str(output_path)]
            if "expected_feet" in entry:
                check_args += ["--expected-feet", str(entry["expected_feet"])]
            result = subprocess.run(check_args)
            if result.returncode != 0:
                failed += 1

    if ran == 0:
        print("no regression corpus files present locally -- nothing to check")
        return 0

    print(f"\n{ran - failed}/{ran} regression corpus file(s) passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
