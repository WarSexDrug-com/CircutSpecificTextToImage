import asyncio

from ..config import settings
from ..models import GenerateRequest, JobStatus, LayerInfo
from .ai_generate import generate_image
from .assemble import assemble_single_layer_svg, assemble_svg
from .quantize import quantize_image
from .separate import separate_layers
from .validate import validate_svg
from .vectorize import vectorize_mask

jobs: dict[str, JobStatus] = {}


def _update(job_id: str, **kwargs):
    if job_id in jobs:
        for key, value in kwargs.items():
            setattr(jobs[job_id], key, value)


async def run_pipeline(request: GenerateRequest, job_id: str) -> str:
    try:
        _update(job_id, status="processing", stage="generating", progress=0.05)
        raster = await generate_image(request.prompt, request.num_layers)
        source_size = raster.width
        if raster.width != raster.height:
            raise ValueError("Image generation returned a non-square image; SVG tracing currently requires a square canvas.")
        _update(job_id, progress=0.3, stage="quantizing")

        quantized, palette = await asyncio.to_thread(
            quantize_image, raster, request.num_layers, request.palette, request.include_background
        )
        _update(job_id, progress=0.45, stage="separating", palette=palette)

        masks = await asyncio.to_thread(separate_layers, quantized, palette)
        _update(job_id, progress=0.55, stage="vectorizing")

        vector_layers = []
        for index, (color, mask) in enumerate(masks):
            paths = await asyncio.to_thread(
                vectorize_mask, mask, request.filter_speckle, request.corner_threshold
            )
            if not paths:
                raise ValueError(f"Could not trace a shape for layer {index + 1} ({color}). Try another prompt or palette.")
            vector_layers.append((color, paths))
            _update(job_id, progress=0.55 + 0.3 * (index + 1) / len(masks))

        _update(job_id, stage="assembling", progress=0.9)
        svg_content = assemble_svg(vector_layers, canvas_inches=request.canvas_inches, source_size=source_size)
        validation = validate_svg(svg_content)
        if not validation.is_valid:
            raise ValueError("; ".join(validation.warnings))

        output_dir = settings.output_dir / job_id
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "design.svg").write_text(svg_content, encoding="utf-8")
        raster.save(output_dir / "preview.png")

        layer_infos = []
        for index, (color, paths) in enumerate(vector_layers):
            layer_svg = assemble_single_layer_svg(
                color, paths, index + 1,
                canvas_inches=request.canvas_inches,
                source_size=source_size,
            )
            (output_dir / f"layer_{index + 1}.svg").write_text(layer_svg, encoding="utf-8")
            from .assemble import _color_label
            layer_infos.append(LayerInfo(index=index + 1, color=color, label=_color_label(color), path_count=len(paths)))

        _update(
            job_id,
            status="complete", stage="done", progress=1.0, layers=layer_infos,
            preview_url=f"/api/preview/{job_id}", download_url=f"/api/download/{job_id}",
        )
    except Exception as error:
        _update(job_id, status="error", stage="error", error=str(error))
    return job_id


