import asyncio
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles

from .config import settings
from .models import GenerateRequest, JobStatus, PalettePreset
from .pipeline.orchestrator import jobs, run_pipeline

app = FastAPI(title="Cricut SVG Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).parent / "static"

PRESET_PALETTES = [
    PalettePreset(name="Cricut Basics", colors=["#000000", "#FF0000", "#0057B7", "#FFFFFF", "#FFD700", "#228B22"]),
    PalettePreset(name="Earth Tones", colors=["#8B4513", "#D2691E", "#DEB887", "#556B2F", "#2F4F4F", "#F5DEB3"]),
    PalettePreset(name="Pastels", colors=["#FFB3BA", "#BAFFC9", "#BAE1FF", "#FFFFBA", "#E8BAFF", "#FFD9BA"]),
    PalettePreset(name="Bold & Bright", colors=["#FF0000", "#FF8C00", "#FFD700", "#00C853", "#2979FF", "#AA00FF"]),
    PalettePreset(name="Monochrome", colors=["#000000", "#333333", "#666666", "#999999", "#CCCCCC", "#FFFFFF"]),
    PalettePreset(name="Halloween", colors=["#FF6600", "#000000", "#800080", "#00FF00", "#FFD700"]),
    PalettePreset(name="Christmas", colors=["#CC0000", "#006400", "#FFD700", "#FFFFFF", "#8B0000"]),
    PalettePreset(name="Ocean", colors=["#003366", "#006994", "#40E0D0", "#87CEEB", "#F0F8FF", "#00CED1"]),
]


@app.post("/api/generate")
async def generate(request: GenerateRequest):
    job_id = uuid4().hex[:12]
    jobs[job_id] = JobStatus(job_id=job_id, status="processing", stage="starting", progress=0.0)
    asyncio.create_task(run_pipeline(request, job_id))
    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/preview/{job_id}")
async def get_preview(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    svg_path = settings.output_dir / job_id / "design.svg"
    if not svg_path.exists():
        raise HTTPException(status_code=404, detail="SVG not yet generated")
    return Response(content=svg_path.read_text(encoding="utf-8"), media_type="image/svg+xml")


@app.get("/api/download/{job_id}")
async def download_svg(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    svg_path = settings.output_dir / job_id / "design.svg"
    if not svg_path.exists():
        raise HTTPException(status_code=404, detail="SVG not yet generated")
    return FileResponse(svg_path, filename=f"cricut_design_{job_id}.svg", media_type="image/svg+xml")


@app.get("/api/download/{job_id}/layer/{layer_num}")
async def download_layer(job_id: str, layer_num: int):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    layer_path = settings.output_dir / job_id / f"layer_{layer_num}.svg"
    if not layer_path.exists():
        raise HTTPException(status_code=404, detail="Layer not found")
    return FileResponse(layer_path, filename=f"layer_{layer_num}.svg", media_type="image/svg+xml")


@app.get("/api/raster-preview/{job_id}")
async def get_raster_preview(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    png_path = settings.output_dir / job_id / "preview.png"
    if not png_path.exists():
        raise HTTPException(status_code=404, detail="Preview not yet generated")
    return FileResponse(png_path, media_type="image/png")


@app.get("/api/palettes")
async def get_palettes():
    return PRESET_PALETTES


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
