"""Render the generated data.scad file consumed by run_template.scad."""


def render_data_scad(lip_cut_z, input_stl_path, xy_bbox):
    escaped_path = str(input_stl_path).replace("\\", "\\\\").replace('"', '\\"')
    min_x, min_y, max_x, max_y = xy_bbox
    return (
        f"lip_cut_z = {lip_cut_z};\n"
        f'input_stl = "{escaped_path}";\n'
        f"input_xy_bbox = [[{min_x}, {min_y}], [{max_x}, {max_y}]];\n"
    )
