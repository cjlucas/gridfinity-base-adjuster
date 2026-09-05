#!/usr/bin/env python3
"""Run gfladjust + invariant checks against every file in the local
real-world lip regression corpus (tests/fixtures/lip_regression_corpus/).

The corpus's STL files are gitignored (see that directory's README for
why) -- entries whose file isn't present locally are skipped with a
note, not failed, so this is always safe to run on a fresh clone.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

CORPUS_DIR = Path(__file__).parent / "fixtures" / "lip_regression_corpus"
MANIFEST = CORPUS_DIR / "manifest.json"
CHECK_OUTPUT = Path(__file__).parent / "check_lip_output.py"


def main():
    manifest = json.loads(MANIFEST.read_text())
    if not manifest:
        print("lip regression corpus manifest is empty")
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
                [sys.executable, "-m", "gfladjust", str(input_path), "-o", str(output_path)],
                cwd=Path(__file__).parent.parent,
                capture_output=True,
                text=True,
            )

            if entry.get("expect_no_lip"):
                if result.returncode == 0:
                    print(f"FAIL {entry['file']}: expected 'no lip detected' but gfladjust succeeded")
                    failed += 1
                else:
                    print("OK   correctly reported no lip / refused to guess")
                continue

            if result.returncode != 0:
                print(f"FAIL {entry['file']}: gfladjust exited with {result.returncode}: {result.stderr.strip()}")
                failed += 1
                continue

            check_args = [
                sys.executable, str(CHECK_OUTPUT), str(input_path), str(output_path),
                "--expected-lip-height", str(entry["expected_lip_height"]),
            ]
            result = subprocess.run(check_args)
            if result.returncode != 0:
                failed += 1

    if ran == 0:
        print("no lip regression corpus files present locally -- nothing to check")
        return 0

    print(f"\n{ran - failed}/{ran} lip regression corpus file(s) passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
