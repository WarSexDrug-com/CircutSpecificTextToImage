import re

from pydantic import BaseModel, Field, field_validator


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    num_layers: int = Field(ge=2, le=8, default=4)
    palette: list[str] | None = None
    canvas_inches: float = Field(ge=1, le=24, default=12.0)
    include_background: bool = False
    filter_speckle: int = Field(ge=1, le=20, default=4)
    corner_threshold: int = Field(ge=10, le=180, default=60)

    @field_validator("palette")
    @classmethod
    def validate_palette(cls, palette):
        if palette is not None and (len(palette) < 2 or len(palette) > 8):
            raise ValueError("Palette must contain between 2 and 8 colors")
        if palette is not None and any(not re.fullmatch(r"#[0-9a-fA-F]{6}", color) for color in palette):
            raise ValueError("Palette colors must use #RRGGBB format")
        return palette


class LayerInfo(BaseModel):
    index: int
    color: str
    label: str
    path_count: int


class JobStatus(BaseModel):
    job_id: str
    status: str = "pending"
    stage: str = ""
    progress: float = 0.0
    preview_url: str | None = None
    download_url: str | None = None
    layers: list[LayerInfo] | None = None
    palette: list[str] | None = None
    error: str | None = None


class PalettePreset(BaseModel):
    name: str
    colors: list[str]

