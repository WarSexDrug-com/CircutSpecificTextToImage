import numpy as np
from PIL import Image
from scipy import ndimage

from .quantize import hex_to_rgb


def separate_layers(
    quantized_image: Image.Image,
    palette: list[str],
) -> list[tuple[str, Image.Image]]:
    img_array = np.array(quantized_image.convert("RGB"))
    layers = []

    for hex_color in palette:
        target = np.array(hex_to_rgb(hex_color), dtype=np.uint8)
        mask = np.all(np.abs(img_array.astype(np.int16) - target.astype(np.int16)) < 5, axis=2)

        struct = ndimage.generate_binary_structure(2, 1)
        mask = ndimage.binary_opening(mask, structure=struct, iterations=1)
        mask = ndimage.binary_closing(mask, structure=struct, iterations=1)

        mask_image = Image.fromarray((mask * 255).astype(np.uint8), mode="L")
        layers.append((hex_color, mask_image))

    return layers
