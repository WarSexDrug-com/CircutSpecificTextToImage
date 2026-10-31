import base64
import io

from openai import AsyncOpenAI
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
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.images.generate(
            model="gpt-image-2",
            prompt=build_prompt(prompt, num_layers),
            size="1024x1024",
            quality="high",
            output_format="png",
            n=1,
        )
        image_data = base64.b64decode(response.data[0].b64_json)
        return Image.open(io.BytesIO(image_data)).convert("RGB")
    finally:
        await client.close()

