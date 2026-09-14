import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from gfbadjust import stl_io

from . import scad_gen
from .lip_detect import LipDetectionError, detect_lip_height

TEMPLATES_DIR = Path(__file__).parent / "templates"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="gfladjust",
        description="Remove a Gridfinity item's stacking lip, auto-detecting its height.",
    )
    parser.add_argument("input", type=Path, help="input STL path")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output STL path")
    parser.add_argument("--openscad-bin", type=str, default=None, help="path to the openscad binary")
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="keep the generated .scad/data files instead of deleting the temp dir",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run detection and emit the generated .scad files only, skip invoking openscad",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def find_openscad(explicit):
    if explicit:
        return explicit
    found = shutil.which("openscad")
    if found:
        return found
    for candidate in (
        "/opt/homebrew/bin/openscad",
        "/usr/local/bin/openscad",
        "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",
    ):
        if Path(candidate).exists():
            return candidate
    raise SystemExit("error: could not find an 'openscad' binary; pass --openscad-bin")


def main(argv=None):
    args = parse_args(argv)

    if not args.input.exists():
        raise SystemExit(f"error: input file not found: {args.input}")

    mesh = stl_io.load_stl(args.input)
    (min_x, min_y, min_z), (max_x, max_y, max_z) = mesh.bbox()
    if args.verbose:
        print(f"bbox: ({min_x:.3f}, {min_y:.3f}, {min_z:.3f}) - ({max_x:.3f}, {max_y:.3f}, {max_z:.3f})")

    try:
        lip_height = detect_lip_height(mesh, verbose=args.verbose)
    except LipDetectionError as e:
        raise SystemExit(f"error: {e}")

    if lip_height <= 0.0:
        raise SystemExit(
            "error: no stacking lip detected (the input's height is already a "
            "clean multiple of the Gridfinity unit height) -- nothing to remove"
        )

    lip_cut_z = max_z - lip_height

    data_scad = scad_gen.render_data_scad(
        lip_cut_z=lip_cut_z,
        input_stl_path=args.input.resolve(),
        xy_bbox=(min_x, min_y, max_x, max_y),
    )

    work_dir = Path(tempfile.mkdtemp(prefix="gfladjust-"))
    try:
        (work_dir / "data.scad").write_text(data_scad)
        shutil.copy(TEMPLATES_DIR / "run_template.scad", work_dir / "run_template.scad")

        if args.dry_run:
            return 0

        openscad_bin = find_openscad(args.openscad_bin)
        rendered_output = work_dir / "output.stl"
        result = subprocess.run(
            [openscad_bin, "-o", str(rendered_output), "run_template.scad"],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )
        if result.stderr and args.verbose:
            print(result.stderr, file=sys.stderr)
        if result.returncode != 0 or not rendered_output.exists():
            print(result.stderr, file=sys.stderr)
            raise SystemExit("error: openscad render failed")

        args.output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(rendered_output, args.output)
        print(f"wrote {args.output} (removed {lip_height:.4f}mm lip)")
        return 0
    finally:
        if args.keep_intermediate or args.dry_run:
            print(f"intermediate files kept in {work_dir}")
        else:
            shutil.rmtree(work_dir, ignore_errors=True)
