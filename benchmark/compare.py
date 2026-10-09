from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageChops, ImageStat


def pixel_diff_max(print_bytes: bytes, kaleido_bytes: bytes) -> float | None:
    img_a = Image.open(BytesIO(print_bytes)).convert('RGB')
    img_b = Image.open(BytesIO(kaleido_bytes)).convert('RGB')
    if img_a.size != img_b.size:
        return None
    diff = ImageChops.difference(img_a, img_b)
    return float(max(channel[1] for channel in diff.getextrema()))


def pixel_diff_mean(print_bytes: bytes, kaleido_bytes: bytes) -> float | None:
    img_a = Image.open(BytesIO(print_bytes)).convert('RGB')
    img_b = Image.open(BytesIO(kaleido_bytes)).convert('RGB')
    if img_a.size != img_b.size:
        return None
    diff = ImageChops.difference(img_a, img_b)
    means = ImageStat.Stat(diff).mean
    return float(sum(means) / len(means))
