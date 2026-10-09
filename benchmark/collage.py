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
    print_bytes: bytes,
    kaleido_bytes: bytes,
    print_label: str,
    kaleido_label: str,
    print_time_s: float,
    kaleido_time_s: float,
    output_path: Path,
) -> None:
    img_print = Image.open(io.BytesIO(print_bytes)).convert('RGBA')
    img_kaleido = Image.open(io.BytesIO(kaleido_bytes)).convert('RGBA')

    w, h = img_print.size
    header_h = 70
    banner_w = w * 2 + 30
    banner_h = h + header_h + 30

    combined = Image.new('RGBA', (banner_w, banner_h), (248, 250, 252, 255))
    draw = ImageDraw.Draw(combined)
    font_header, font_sub = _load_fonts()

    x_print = 10
    y_top = 10
    draw.rounded_rectangle(
        [x_print, y_top, x_print + w, y_top + header_h - 10],
        radius=6,
        fill=(255, 255, 255, 255),
        outline=(226, 232, 240, 255),
        width=1,
    )
    draw.text((x_print + 15, y_top + 12), print_label, fill=(15, 23, 42, 255), font=font_header)
    draw.text(
        (x_print + 15, y_top + 34),
        f'Latency: {print_time_s * 1000:.1f} ms',
        fill=(16, 149, 193, 255),
        font=font_sub,
    )
    combined.paste(img_print, (x_print, y_top + header_h), img_print)

    x_k = w + 20
    draw.rounded_rectangle(
        [x_k, y_top, x_k + w, y_top + header_h - 10],
        radius=6,
        fill=(255, 255, 255, 255),
        outline=(226, 232, 240, 255),
        width=1,
    )
    draw.text((x_k + 15, y_top + 12), kaleido_label, fill=(15, 23, 42, 255), font=font_header)
    draw.text(
        (x_k + 15, y_top + 34),
        f'Latency: {kaleido_time_s * 1000:.1f} ms',
        fill=(100, 116, 139, 255),
        font=font_sub,
    )
    combined.paste(img_kaleido, (x_k, y_top + header_h), img_kaleido)

    draw.rectangle(
        [x_print, y_top + header_h, x_print + w, y_top + header_h + h], outline=(226, 232, 240, 255), width=1
    )
    draw.rectangle([x_k, y_top + header_h, x_k + w, y_top + header_h + h], outline=(226, 232, 240, 255), width=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.save(output_path, 'PNG')
