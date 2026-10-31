import asyncio
import io
from urllib.parse import quote

import httpx
from PIL import Image

from ..config import settings


def build_prompt(user_prompt: str, num_layers: int) -> str:
    return (
        f"A flat-color vector illustration of {user_prompt}. "
        f"Paper cut art style with at most {num_layers} distinct solid color regions. "
        "Bold clean outlines, no gradients, shadows, textures, or shading. "
        "Use simple, separate shapes suitable for layered paper crafts or vinyl cutting. "
        "Isolated on a pure white background."
    )


async def generate_image(prompt: str, num_layers: int) -> Image.Image:
    full_prompt = build_prompt(prompt, num_layers)
    encoded_prompt = quote(full_prompt)
    size = settings.default_image_size
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={size}&height={size}&nologo=true"

    last_error = None
    for attempt in range(4):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.get(url, follow_redirects=True)
                if response.status_code == 200:
                    image = Image.open(io.BytesIO(response.content)).convert("RGB")
                    return image
                last_error = f"HTTP {response.status_code}"
        except httpx.TimeoutException:
            last_error = "Request timed out"
        except httpx.ConnectError:
            last_error = "Connection failed"

        if attempt < 3:
            await asyncio.sleep(3 * (attempt + 1))

    raise RuntimeError(f"Image generation failed after 4 attempts: {last_error}")
