from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ai_backend: str = "openai"
    openai_api_key: str = ""
    output_dir: Path = Path("./app/output")
    default_image_size: int = 1024
    max_layers: int = 8
    svg_dpi: int = 72
    svg_canvas_inches: float = 12.0

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
