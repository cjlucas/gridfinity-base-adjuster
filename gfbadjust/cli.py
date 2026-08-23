import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from . import gridfit, rasterize, scad_gen, stl_io
from .constants import DEFAULT_INPUT_BASE_HEIGHT
from .geometry import loop_bbox, main_loop
from .slicing import plane_slice

# A loop from the same slice as the main outer boundary is only suspicious
# (suggests --base-height sliced into the hollow body, producing a large
# nested interior loop) if it's not small relative to the main loop --
# small internal features (holes, divider/slot gaps) are normal and not
# a sign of anything wrong.
SUSPICIOUS_LOOP_AREA_FRACTION = 0.2

TEMPLATES_DIR = Path(__file__).parent / "templates"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="gfbadjust",
        description="Replace a Gridfinity item's base with a freshly generated one.",
    )
    parser.add_argument("input", type=Path, help="input STL path")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output STL path")
    parser.add_argument(
        "--base-height",
        type=float,
        default=DEFAULT_INPUT_BASE_HEIGHT,
        help=(
            "expected height of the *existing* base to cut off "
            f"(default {DEFAULT_INPUT_BASE_HEIGHT}; adjust if your input "
            "uses a different base height)"
        ),
    )
    parser.add_argument(
        "--grid-origin",
        type=str,
        default=None,
        help="manual override 'X,Y' for the 42mm grid origin, skips auto-detection",
    )
    parser.add_argument(
        "--footprint-height",
        type=float,
        default=0.2,
        help="height above the cut plane to slice the footprint at (default 0.2)",
    )
    parser.add_argument("--openscad-bin", type=str, default=None, help="path to the openscad binary")
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="keep the generated .scad/data files instead of deleting the temp dir",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run analysis and emit the generated .scad files only, skip invoking openscad",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


def find_openscad(explicit):
    if explicit:
        return explicit
    found = shutil.which("openscad")
    if found:
        return found
    for candidate in ("/opt/homebrew/bin/openscad", "/usr/local/bin/openscad"):
        if Path(candidate).exists():
            return candidate
    raise SystemExit("error: could not find an 'openscad' binary; pass --openscad-bin")


def render_occupancy_grid(occupied_cells, nx, ny):
    occupied_set = set(occupied_cells)
    lines = []
    for iy in range(ny - 1, -1, -1):
        row = "".join("#" if (ix, iy) in occupied_set else "." for ix in range(nx))
        lines.append(row)
    return "\n".join(lines)


def main(argv=None):
    args = parse_args(argv)

    if not args.input.exists():
        raise SystemExit(f"error: input file not found: {args.input}")

    mesh = stl_io.load_stl(args.input)
    (min_x, min_y, min_z), (max_x, max_y, max_z) = mesh.bbox()
    if args.verbose:
        print(f"bbox: ({min_x:.3f}, {min_y:.3f}, {min_z:.3f}) - ({max_x:.3f}, {max_y:.3f}, {max_z:.3f})")

    cut_z = min_z + args.base_height

    loops = plane_slice(mesh, cut_z + args.footprint_height)
    if not loops:
        raise SystemExit(
            f"error: no footprint found at z={cut_z + args.footprint_height:.3f}; "
            "check --base-height/--footprint-height"
        )
    if len(loops) > 1:
        main = main_loop(loops)
        main_bbox = loop_bbox(main)
        main_area = (main_bbox[2] - main_bbox[0]) * (main_bbox[3] - main_bbox[1])
        suspicious = [l for l in loops if l is not main]
        big_suspicious = [
            l for l in suspicious
            if (lambda b: (b[2] - b[0]) * (b[3] - b[1]))(loop_bbox(l)) / main_area
            >= SUSPICIOUS_LOOP_AREA_FRACTION
        ]
        if big_suspicious:
            print(
                f"warning: footprint slice found {len(big_suspicious)} large "
                "secondary loop(s) alongside the main outline. If this bin "
                "doesn't actually have a hole/multiple islands, --base-height "
                "is probably too tall and you're slicing through the hollow "
                "body instead of the solid base/floor -- try a smaller value.",
                file=sys.stderr,
            )

    if args.grid_origin:
        gx, gy = (float(v) for v in args.grid_origin.split(","))
        grid_origin = (gx, gy)
    else:
        grid_origin = gridfit.compute_grid_origin(loops)

    occupied_cells, nx, ny = rasterize.rasterize(loops, grid_origin)
    if not occupied_cells:
        raise SystemExit(
            "error: no occupied cells detected in the footprint. This usually "
            "means --base-height doesn't match this file's actual base height (the "
            "footprint slice landed inside the hollow body rather than at the solid "
            "floor). Re-run with -v to inspect the bbox/loops, and try adjusting "
            "--base-height."
        )

    if args.verbose:
        print(f"grid origin: ({grid_origin[0]:.3f}, {grid_origin[1]:.3f})")
        print(f"occupied cells ({len(occupied_cells)}/{nx * ny}):")
        print(render_occupancy_grid(occupied_cells, nx, ny))

    data_scad = scad_gen.render_data_scad(
        cut_z=cut_z,
        grid_origin=grid_origin,
        input_stl_path=args.input.resolve(),
        occupied_cells=occupied_cells,
        xy_bbox=(min_x, min_y, max_x, max_y),
    )

    work_dir = Path(tempfile.mkdtemp(prefix="gfbadjust-"))
    try:
        (work_dir / "data.scad").write_text(data_scad)
        shutil.copy(TEMPLATES_DIR / "gridfinity_base.scad", work_dir / "gridfinity_base.scad")
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
        print(f"wrote {args.output}")
        return 0
    finally:
        if args.keep_intermediate or args.dry_run:
            print(f"intermediate files kept in {work_dir}")
        else:
            shutil.rmtree(work_dir, ignore_errors=True)
