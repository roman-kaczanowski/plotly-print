from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, BinaryIO

import resvg_py
from PIL import Image

from plotly_print.fonts import FONT_SUFFIXES, FontPaths, resolve_font_dirs, resolve_font_files

SYSTEM_FONT_DIRS = [
    '/System/Library/Fonts/Supplemental',
    '/Library/Fonts',
    '/System/Library/Fonts',
    '/usr/share/fonts',
    '/usr/local/share/fonts',
    'C:\\Windows\\Fonts',
]
_BUNDLED_FONT_FILES = sorted(str(path) for path in (Path(__file__).resolve().parent / '_fonts').glob('*.ttf'))
# System family preferences first, then the bundled family used when none is installed.
_BUNDLED_FALLBACKS = {
    'sans_serif_family': (
        ['Arial', 'Helvetica', 'DejaVu Sans', 'Liberation Sans', 'FreeSans'],
        'DejaVu Sans',
    ),
    'serif_family': (['Times New Roman', 'Liberation Serif', 'DejaVu Serif'], 'DejaVu Serif'),
    'monospace_family': (['Courier New', 'Liberation Mono', 'DejaVu Sans Mono'], 'DejaVu Sans Mono'),
}


def _discover_system_fonts() -> tuple[list[str], set[str]]:
    dirs: list[str] = []
    stems: set[str] = set()
    for directory in SYSTEM_FONT_DIRS:
        files = [path for path in Path(directory).rglob('*') if path.is_file() and path.suffix.lower() in FONT_SUFFIXES]
        if files:
            dirs.append(directory)
            stems.update(re.sub(r'[^a-z0-9]', '', path.stem.lower()) for path in files)
    return dirs, stems


EXISTING_FONT_DIRS, _SYSTEM_FONT_STEMS = _discover_system_fonts()

COMMON_FONT_NAMES = [
    'verdana',
    'arial',
    'tahoma',
    'trebuchet ms',
    'helvetica',
    'times new roman',
    'courier new',
    'georgia',
]

_SVG_ROOT_RE = re.compile(r'<svg\b[^>]*>', re.IGNORECASE)
_ATTR_RE = re.compile(r'([^\s=]+)\s*=\s*("([^"]*)"|\'([^\']*)\')')
_LENGTH_RE = re.compile(r'^([+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?)\s*[a-z%]*$', re.IGNORECASE)


def _resvg_font_options(font_files: FontPaths | None = None, font_dirs: FontPaths | None = None) -> dict[str, Any]:
    options: dict[str, Any] = {}
    dirs = resolve_font_dirs(font_dirs) + EXISTING_FONT_DIRS
    if dirs:
        options['font_dirs'] = dirs

    bundled_files = resolve_font_files(font_files) + _BUNDLED_FONT_FILES
    if not bundled_files:
        return options
    options['font_files'] = bundled_files
    if not _BUNDLED_FONT_FILES:
        return options

    for option, (candidates, bundled) in _BUNDLED_FALLBACKS.items():
        for candidate in candidates:
            stem = re.sub(r'[^a-z0-9]', '', candidate.lower())
            if any(system_stem.startswith(stem) for system_stem in _SYSTEM_FONT_STEMS):
                options[option] = candidate
                break
        else:
            options[option] = bundled
    if not dirs:
        options['font_family'] = _BUNDLED_FALLBACKS['sans_serif_family'][1]
    return options


def _normalize_svg_fonts(svg: str) -> str:
    def _cap(m: re.Match[str]) -> str:
        val = m.group(0)
        for name in COMMON_FONT_NAMES:
            val = re.sub(r'\b' + re.escape(name) + r'\b', name.title(), val, flags=re.IGNORECASE)
        return val

    return re.sub(r'font-family:\s*[^;\"}]+', _cap, svg)


def _parse_length(value: str | None) -> float | None:
    if value is None:
        return None
    m = _LENGTH_RE.match(value.strip())
    if not m:
        return None
    return float(m.group(1))


def _parse_svg_layout_size(svg: str) -> tuple[float, float]:
    root = _SVG_ROOT_RE.search(svg)
    if not root:
        raise ValueError('SVG root element not found')

    attrs = {
        m.group(1).lower(): (m.group(3) if m.group(3) is not None else m.group(4))
        for m in _ATTR_RE.finditer(root.group(0))
    }

    width = _parse_length(attrs.get('width'))
    height = _parse_length(attrs.get('height'))

    if (width is None or height is None) and 'viewbox' in attrs:
        parts = attrs['viewbox'].replace(',', ' ').split()
        if len(parts) == 4:
            if width is None:
                width = float(parts[2])
            if height is None:
                height = float(parts[3])

    if width is None or height is None:
        raise ValueError('Could not determine SVG layout width/height')
    return width, height


def _prepare_svg_for_raster(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
) -> str:
    layout_w, layout_h = _parse_svg_layout_size(svg)
    if width is not None:
        layout_w = float(width)
    if height is not None:
        layout_h = float(height)

    out_w = max(1, int(round(layout_w * scale)))
    out_h = max(1, int(round(layout_h * scale)))

    root = _SVG_ROOT_RE.search(svg)
    if not root:
        raise ValueError('SVG root element not found')

    tag = root.group(0)
    existing = {m.group(1).lower() for m in _ATTR_RE.finditer(tag)}

    def _set_attr(tag_str: str, name: str, value: str) -> str:
        pattern = rf'({re.escape(name)}\s*=\s*)("([^"]*)"|\'([^\']*)\')'
        if re.search(pattern, tag_str, flags=re.IGNORECASE):
            return re.sub(pattern, rf'\1"{value}"', tag_str, count=1, flags=re.IGNORECASE)
        return re.sub(r'\s*>$', f' {name}="{value}">', tag_str, count=1)

    new_tag = tag
    new_tag = _set_attr(new_tag, 'width', str(out_w))
    new_tag = _set_attr(new_tag, 'height', str(out_h))
    if 'viewbox' not in existing:
        vb_w = int(layout_w) if layout_w == int(layout_w) else layout_w
        vb_h = int(layout_h) if layout_h == int(layout_h) else layout_h
        new_tag = _set_attr(new_tag, 'viewBox', f'0 0 {vb_w} {vb_h}')

    return svg[: root.start()] + new_tag + svg[root.end() :]


def svg_to_png(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
    font_files: FontPaths | None = None,
    font_dirs: FontPaths | None = None,
) -> bytes:
    normalized_svg = _normalize_svg_fonts(svg)
    prepared = _prepare_svg_for_raster(normalized_svg, width=width, height=height, scale=scale)
    return resvg_py.svg_to_bytes(prepared, **_resvg_font_options(font_files, font_dirs))


def svg_to_jpeg(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
    quality: int = 90,
    font_files: FontPaths | None = None,
    font_dirs: FontPaths | None = None,
) -> bytes:
    png_bytes = svg_to_png(svg, width=width, height=height, scale=scale, font_files=font_files, font_dirs=font_dirs)
    img = Image.open(io.BytesIO(png_bytes))
    if img.mode in ('RGBA', 'LA', 'P'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = bg
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=quality)
    return buf.getvalue()


def svg_to_webp(
    svg: str,
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
    quality: int = 90,
    font_files: FontPaths | None = None,
    font_dirs: FontPaths | None = None,
) -> bytes:
    png_bytes = svg_to_png(svg, width=width, height=height, scale=scale, font_files=font_files, font_dirs=font_dirs)
    img = Image.open(io.BytesIO(png_bytes))
    buf = io.BytesIO()
    img.save(buf, format='WEBP', quality=quality)
    return buf.getvalue()


def write_raster(
    svg: str,
    target: str | BinaryIO,
    format: str = 'png',
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
    font_files: FontPaths | None = None,
    font_dirs: FontPaths | None = None,
) -> None:
    fmt = format.lower().strip()
    if fmt == 'png':
        data = svg_to_png(svg, width=width, height=height, scale=scale, font_files=font_files, font_dirs=font_dirs)
    elif fmt in ('jpg', 'jpeg'):
        data = svg_to_jpeg(svg, width=width, height=height, scale=scale, font_files=font_files, font_dirs=font_dirs)
    elif fmt == 'webp':
        data = svg_to_webp(svg, width=width, height=height, scale=scale, font_files=font_files, font_dirs=font_dirs)
    else:
        raise ValueError(f"Unsupported raster format: {format}. Supported: 'png', 'jpeg', 'webp'")

    if isinstance(target, str):
        Path(target).write_bytes(data)
    else:
        target.write(data)
