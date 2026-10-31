import re

import numpy as np
from PIL import Image
from sklearn.cluster import MiniBatchKMeans


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}"


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", hex_color):
        raise ValueError(f"Invalid color '{hex_color}'; expected #RRGGBB")
    return tuple(int(hex_color[i:i + 2], 16) for i in (1, 3, 5))


def _assign_labels(pixels: np.ndarray, centers: np.ndarray) -> np.ndarray:
    labels = np.empty(len(pixels), dtype=np.int32)
    chunk = 100_000
    for start in range(0, len(pixels), chunk):
        end = min(start + chunk, len(pixels))
        diff = pixels[start:end, None, :].astype(np.float32) - centers[None, :, :].astype(np.float32)
        labels[start:end] = np.argmin(np.sum(diff * diff, axis=2), axis=1)
    return labels


def quantize_image(
    image: Image.Image,
    num_colors: int,
    palette: list[str] | None = None,
    include_background: bool = False,
) -> tuple[Image.Image, list[str]]:
    img_array = np.asarray(image.convert("RGB"))
    height, width, _ = img_array.shape
    pixels = img_array.reshape(-1, 3)

    if palette:
        centers = np.asarray([hex_to_rgb(color) for color in palette], dtype=np.uint8)
    else:
        sample = pixels[::max(1, len(pixels) // 20000)].astype(np.float32)
        n_unique = len(np.unique(sample // 16, axis=0))
        k = min(num_colors, max(2, n_unique))
        kmeans = MiniBatchKMeans(n_clusters=k, n_init=3, random_state=42, batch_size=1000)
        kmeans.fit(sample)
        centers = np.clip(np.rint(kmeans.cluster_centers_), 0, 255).astype(np.uint8)

    labels = _assign_labels(pixels, centers)

    counts = np.bincount(labels, minlength=len(centers))
    keep = counts > 0
    if not include_background:
        near_white = np.all(centers >= 240, axis=1)
        candidates = np.flatnonzero(keep & near_white)
        if candidates.size:
            keep[candidates[np.argmax(counts[candidates])]] = False

    kept_labels = np.flatnonzero(keep)
    if kept_labels.size == 0:
        raise ValueError("No foreground colors remain. Enable the background layer or choose a different palette.")

    kept_labels = kept_labels[np.argsort(-counts[kept_labels])]
    palette_result = [rgb_to_hex(*map(int, centers[label])) for label in kept_labels]
    quantized = centers[labels].reshape(height, width, 3)
    return Image.fromarray(quantized, mode="RGB"), palette_result
