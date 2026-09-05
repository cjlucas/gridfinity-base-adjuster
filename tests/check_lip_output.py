#!/usr/bin/env python3
"""Run gfladjust's correctness invariants against an input/output STL pair.

Usage:
    python3 tests/check_lip_output.py INPUT.stl OUTPUT.stl --expected-lip-height MM

Used by the synthetic-fixture end-to-end test, and just as usefully for
ad hoc checks whenever you try gfladjust against a new real-world file.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import lip_invariants
from gfbadjust import stl_io


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-lip-height", type=float, required=True)
    parser.add_argument("--tol", type=float, default=0.05, help="allowed Z drift in mm")
    parser.add_argument("--bbox-tol", type=float, default=0.5, help="allowed XY bbox drift in mm")
    args = parser.parse_args()

    input_mesh = stl_io.load_stl(args.input)
    output_mesh = stl_io.load_stl(args.output)

    failed = []

    def check(name, fn):
        try:
            result = fn()
            suffix = f" ({result})" if result is not None else ""
            print(f"OK   {name}{suffix}")
        except lip_invariants.InvariantError as e:
            print(f"FAIL {name}: {e}")
            failed.append(name)

    check("output is non-empty", lambda: _require(output_mesh.triangles, "no triangles in output"))
    check(
        "output height matches input minus detected lip",
        lambda: lip_invariants.check_output_height(
            input_mesh, output_mesh, args.expected_lip_height, args.tol
        ),
    )
    check(
        "output XY bbox matches input",
        lambda: lip_invariants.check_xy_bbox_preserved(input_mesh, output_mesh, args.bbox_tol),
    )

    if failed:
        print(f"\n{len(failed)} check(s) failed: {', '.join(failed)}")
        sys.exit(1)
    print("\nall checks passed")


def _require(cond, msg):
    if not cond:
        raise lip_invariants.InvariantError(msg)
    return None


if __name__ == "__main__":
    main()
