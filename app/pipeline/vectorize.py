import io
import re

import vtracer
from PIL import Image


def _extract_paths(svg_string: str) -> list[str]:
    return re.findall(r'd="([^"]+)"', svg_string)


def _count_nodes(path_d: str) -> int:
    return len(re.findall(r"[MmLlHhVvCcSsQqTtAaZz]", path_d))


def vectorize_mask(
    mask: Image.Image,
    filter_speckle: int = 4,
    corner_threshold: int = 60,
    length_threshold: float = 4.0,
    splice_threshold: int = 45,
    path_precision: int = 2,
) -> list[str]:
    buf = io.BytesIO()
    mask.convert("RGBA").save(buf, format="PNG")
    svg_str = vtracer.convert_raw_image_to_svg(
        buf.getvalue(), img_format="png", colormode="binary",
        filter_speckle=filter_speckle, corner_threshold=corner_threshold,
        length_threshold=length_threshold, splice_threshold=splice_threshold,
        path_precision=path_precision,
    )
    # Preserve vtracer's original commands: appending Z to open curves changes their geometry.
    return [path for path in _extract_paths(svg_str) if _count_nodes(path) > 1]
