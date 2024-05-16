from __future__ import annotations

import math
import pathlib
import typing as ty
import numpy

from tqec.templates.base import Template
from tqec.templates.composed import ComposedTemplate


def display_template(
    template: Template, plaquette_indices: ty.Sequence[int] | None = None
) -> None:
    """Display a template instance with ASCII output.

    Args:
        template: the Template instance to display.
        plaquette_indices: the plaquette indices that are forwarded to the call
            to `template.instantiate` to get the actual template representation.
            If None, default to ``range(1, template.expected_plaquettes_number + 1)``.
    """
    if plaquette_indices is None:
        plaquette_indices = tuple(range(1, template.expected_plaquettes_number + 1))
    arr = template.instantiate(plaquette_indices)
    for line in arr:
        for element in line:
            element = str(element) if element != 0 else "."
            print(f"{element:>3}", end="")
        print()


def display_templates_ascii(
    templates: ComposedTemplate,
    plaquette_indices: ty.Sequence[int] | None = None,
) -> None:
    """Display the templates as an ASCII art (multi-line string).

    Args:
        templates: the ComposedTemplate instance to display.
        *plaquette_indices: the plaquette indices that are forwarded to the call
            to `template.instantiate` to get the actual template representation.
    """
    if plaquette_indices is None:
        plaquette_indices = tuple(range(1, templates.expected_plaquettes_number + 1))
    # Numpy array including all templates.
    arr = templates.instantiate(plaquette_indices)
    # Upper-left and bottom-right corners of every template, expressed as (row, column) of the array returned.
    ul_pos = {}
    br_pos = {}
    ul_positions = templates._compute_ul_absolute_position()
    bbul, _ = templates._get_bounding_box_from_ul_positions(ul_positions)
    for tid, tul in ul_positions.items():
        # We follow the same procedure as in Template.instantiate():
        # Subtracting bbul (upper-left bounding box position) from each coordinate to stick
        # the represented code to the axes and avoid having negative indices.
        x = tul.x - bbul.x
        y = tul.y - bbul.y
        # Recall that numpy indexing is (y, x) in our coordinate system convention.
        tshapey, tshapex = templates._templates[tid].shape.to_numpy_shape()
        ul_pos[tid] = (y, x)
        br_pos[tid] = (y + tshapey, x + tshapex)
    # Format of the ASCII art.   
    h_space = 5
    empty_line = ' '*numpy.shape(arr)[1]*h_space
    cross_mark = '■'
    # Instead of print to screen, we create a multi-line buffer string.
    # when completed, we print the buffer.
    buffer_lines = []
    buffer_lines.append(empty_line)
    for line in arr:
        buffer = ''
        for element in line:
            element = str(element) if element != 0 else "."
            buffer += f"{element:^{h_space}}"
        buffer_lines.append(buffer)
        buffer_lines.append(empty_line)
    # Add separations of the templates.
    for tid, tul in ul_pos.items():
        col = tul[1] * h_space
        num_h_sep = br_pos[tid][1]*h_space - col
        # Add horizontal lines at the top and bottom.
        for row in [tul[0], br_pos[tid][0]]:
        #for row in [tul[0]]:
        #for row in [br_pos[tid][0]]:
            row *= 2
            line = buffer_lines[row]
            line = line[:col] + cross_mark + '-'*(num_h_sep-1) + cross_mark + line[col+num_h_sep+1:]
            buffer_lines[row] = line
        # Add vertical lines on the left and right.
        for col in [tul[1], br_pos[tid][1]]:
            col *= h_space
            for row in range(tul[0]*2+1, br_pos[tid][0]*2):
                line = buffer_lines[row]
                line = line[:col] + '|' + line[col+1:]
                buffer_lines[row] = line
    for line in buffer_lines:
        print(line)


def display_templates_svg(
    templates: ComposedTemplate,
    write_svg_file: str | pathlib.Path | None,
    canvas_height: int = 500,
    *plaquette_indices: int,
) -> str:
    """Display the templates as an SVG file.

    This function is useful to debug the templates and their relative positions.
    However, note that the implementation iterates over all the plaquettes of all
    the templates, it can be very slow for large templates and results in huge
    svg files.

    Args:
        templates: the ComposedTemplate instance to display.
        write_svg_file: the path to the SVG file to write.
        canvas_height: the height of the canvas in pixels to draw on.
        *plaquette_indices: the plaquette indices that are forwarded to the call
            to `template.instantiate` to get the actual template representation.

    Returns:
        the SVG string.
    """
    if len(plaquette_indices) == 0:
        plaquette_indices = tuple(range(1, templates.expected_plaquettes_number + 1))
    template_list = templates._templates
    ul_positions = templates._compute_ul_absolute_position()
    box = templates._get_bounding_box_from_ul_positions(ul_positions)
    box_width: float = box[1].x - box[0].x
    box_height: float = box[1].y - box[0].y
    pad = max(box_width, box_height) * 0.1
    box_width += pad
    box_height += pad
    scale_factor = canvas_height / box_height
    canvas_width = int(math.ceil(box_width * scale_factor))

    def rect(
        x: int, y: int, width: int, height: int, label: int = 0, outmost: bool = False
    ) -> list[str]:
        x_scaled = (x - box[0].x + pad / 2) * scale_factor
        y_scaled = (y - box[0].y + pad / 2) * scale_factor
        width_scaled = width * scale_factor
        height_scaled = height * scale_factor
        lines: list[str] = []
        stroke = "#00FF00" if outmost else "black"
        stroke_width = 3 if outmost else 2
        # Draw the rectangle
        lines.append(
            f'<rect x="{x_scaled}" '
            f'y="{y_scaled}" '
            f'width="{width_scaled}" '
            f'height="{height_scaled}" '
            f'stroke="{stroke}" '
            f'stroke-width="{stroke_width}" '
            'fill="none" />'
        )
        # Draw the plaquette index
        if label:
            lines.append(
                f'<text x="{x_scaled + width_scaled / 2}" '
                f'y="{y_scaled + height_scaled / 2}" '
                'font-size="10" '
                'text-anchor="middle" '
                f'dominant-baseline="middle">{label}</text>'
            )
        return lines

    svg_header = f"""<svg viewBox="0 0 {canvas_width} {canvas_height}" xmlns="http://www.w3.org/2000/svg">"""
    # Draw the shape rectangles at the top of
    # the plaquette rectangles
    outer_rects = []
    inner_rects = []
    svg_lines = [svg_header]

    for i, template in enumerate(template_list):
        ul_position = ul_positions[i]
        indices = [
            plaquette_indices[k]
            for k in templates._relative_position_graph.nodes[i]["plaquette_indices"]
        ]
        arr = template.instantiate(indices)
        outer_rects.extend(
            rect(ul_position.x, ul_position.y, len(arr[0]), len(arr), outmost=True)
        )
        for shape_y, line in enumerate(arr):
            for shape_x, element in enumerate(line):
                if element == 0:
                    continue
                x = ul_position.x + shape_x
                y = ul_position.y + shape_y
                inner_rects.extend(rect(x, y, 1, 1, element))

    svg_lines.extend(inner_rects)
    svg_lines.extend(outer_rects)
    svg_lines.append("</svg>")

    svg_str = "\n".join(svg_lines)
    # Write the SVG file
    if write_svg_file is not None:
        with open(write_svg_file, "w") as f:
            f.write(svg_str)
    return svg_str
