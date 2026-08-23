"""Render the generated data.scad file consumed by run_template.scad."""


def render_data_scad(cut_z, grid_origin, input_stl_path, occupied_cells):
    escaped_path = str(input_stl_path).replace("\\", "\\\\").replace('"', '\\"')
    cells_str = ", ".join(f"[{ix}, {iy}]" for (ix, iy) in occupied_cells)
    return (
        f"cut_z = {cut_z};\n"
        f"grid_origin = [{grid_origin[0]}, {grid_origin[1]}];\n"
        f'input_stl = "{escaped_path}";\n'
        f"occupied_cells = [{cells_str}];\n"
    )
