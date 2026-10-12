from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = (
    '/System/Library/Fonts/Supplemental/Verdana Bold.ttf',
    '/System/Library/Fonts/Supplemental/Verdana.ttf',
    '/Library/Fonts/Arial.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
)


def _load_fonts() -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    try:
        return (
            ImageFont.truetype(_FONT_CANDIDATES[0], 16),
            ImageFont.truetype(_FONT_CANDIDATES[1], 13),
        )
    except OSError:
        default = ImageFont.load_default()
        return default, default


def build_side_by_side(
    before_bytes: bytes,
    after_bytes: bytes,
    before_label: str,
    after_label: str,
    before_time_s: float,
    after_time_s: float,
    output_path: Path,
) -> None:
    """Left = before (baseline), right = after (candidate)."""
    img_before = Image.open(io.BytesIO(before_bytes)).convert('RGBA')
    img_after = Image.open(io.BytesIO(after_bytes)).convert('RGBA')

    w, h = img_before.size
    header_h = 70
    banner_w = w * 2 + 30
    banner_h = h + header_h + 30

    combined = Image.new('RGBA', (banner_w, banner_h), (248, 250, 252, 255))
    draw = ImageDraw.Draw(combined)
    font_header, font_sub = _load_fonts()

    def _panel(x: int, img: Image.Image, label: str, time_s: float, accent: tuple[int, int, int, int]) -> None:
        y_top = 10
        draw.rounded_rectangle(
            [x, y_top, x + w, y_top + header_h - 10],
            radius=6,
            fill=(255, 255, 255, 255),
            outline=(226, 232, 240, 255),
            width=1,
        )
        draw.text((x + 15, y_top + 12), label, fill=(15, 23, 42, 255), font=font_header)
        draw.text((x + 15, y_top + 34), f'Latency: {time_s * 1000:.1f} ms', fill=accent, font=font_sub)
        combined.paste(img, (x, y_top + header_h), img)
        draw.rectangle(
            [x, y_top + header_h, x + w, y_top + header_h + h],
            outline=(226, 232, 240, 255),
            width=1,
        )

    _panel(10, img_before, before_label, before_time_s, (100, 116, 139, 255))
    _panel(w + 20, img_after, after_label, after_time_s, (16, 149, 193, 255))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.save(output_path, 'PNG')
