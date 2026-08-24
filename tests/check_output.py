#!/usr/bin/env python3
"""Run gfbadjust's correctness invariants against an input/output STL pair.

Usage:
    python3 tests/check_output.py INPUT.stl OUTPUT.stl [--expected-feet N]

Used by the synthetic-fixture end-to-end test, and just as usefully for
ad hoc checks whenever you try gfbadjust against a new real-world file --
run this on the pair afterward instead of hand-writing a one-off debug
script. If you don't know the expected foot count, omit --expected-feet
and the other (input-independent) invariants still run.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import invariants
from gfbadjust import stl_io


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--expected-feet", type=int, default=None)
    parser.add_argument("--at-height", type=float, default=0.5, help="height above min Z to sample feet at")
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
        except invariants.InvariantError as e:
            print(f"FAIL {name}: {e}")
            failed.append(name)

    check("output is non-empty", lambda: _require(output_mesh.triangles, "no triangles in output"))
    check(
        "all feet are 21mm-scale",
        lambda: invariants.check_all_feet_are_21mm_scale(output_mesh, args.at_height),
    )
    check(
        "output XY bbox matches input",
        lambda: invariants.check_xy_bbox_preserved(input_mesh, output_mesh, args.bbox_tol),
    )
    if args.expected_feet is not None:
        check(
            "foot count matches expected",
            lambda: invariants.check_foot_count(output_mesh, args.expected_feet, args.at_height),
        )

    if failed:
        print(f"\n{len(failed)} check(s) failed: {', '.join(failed)}")
        sys.exit(1)
    print("\nall checks passed")


def _require(cond, msg):
    if not cond:
        raise invariants.InvariantError(msg)
    return None


if __name__ == "__main__":
    main()
