import svgwrite

from .quantize import hex_to_rgb

COLOR_NAMES = {
    (255, 0, 0): "Red", (0, 255, 0): "Green", (0, 0, 255): "Blue",
    (255, 255, 0): "Yellow", (255, 0, 255): "Magenta", (0, 255, 255): "Cyan",
    (0, 0, 0): "Black", (255, 255, 255): "White",
    (255, 165, 0): "Orange", (128, 0, 128): "Purple",
    (255, 192, 203): "Pink", (165, 42, 42): "Brown",
}


def _color_label(hex_color: str) -> str:
    rgb = hex_to_rgb(hex_color)
    if rgb in COLOR_NAMES:
        return COLOR_NAMES[rgb]

    best_name = "Color"
    best_dist = float("inf")
    for known_rgb, name in COLOR_NAMES.items():
        dist = sum((a - b) ** 2 for a, b in zip(rgb, known_rgb))
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name


def assemble_svg(
    vector_layers: list[tuple[str, list[str]]],
    canvas_inches: float = 12.0,
    source_size: int = 1024,
) -> str:
    canvas_units = int(canvas_inches * 72)
    scale = canvas_units / source_size

    dwg = svgwrite.Drawing(
        size=(f"{canvas_units}px", f"{canvas_units}px"),
        viewBox=f"0 0 {canvas_units} {canvas_units}",
    )
    dwg.attribs["version"] = "1.1"
    

    for i, (hex_color, paths) in enumerate(vector_layers):
        label = _color_label(hex_color)
        group = dwg.g(
            id=f"Layer_{i + 1}_{label}",
            fill=hex_color,
            stroke="none",
            transform=f"scale({scale:.6f})",
        )
        for path_d in paths:
            group.add(dwg.path(d=path_d))
        dwg.add(group)

    return dwg.tostring()


def assemble_single_layer_svg(
    hex_color: str,
    paths: list[str],
    layer_index: int,
    canvas_inches: float = 12.0,
    source_size: int = 1024,
) -> str:
    canvas_units = int(canvas_inches * 72)
    scale = canvas_units / source_size

    dwg = svgwrite.Drawing(
        size=(f"{canvas_units}px", f"{canvas_units}px"),
        viewBox=f"0 0 {canvas_units} {canvas_units}",
    )
    dwg.attribs["version"] = "1.1"
    

    label = _color_label(hex_color)
    group = dwg.g(
        id=f"Layer_{layer_index}_{label}",
        fill=hex_color,
        stroke="none",
        transform=f"scale({scale:.6f})",
    )
    for path_d in paths:
        group.add(dwg.path(d=path_d))
    dwg.add(group)

    return dwg.tostring()

