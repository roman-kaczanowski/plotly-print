from __future__ import annotations

import os
from typing import Any, BinaryIO

from plotly_print.engine import get_engine
from plotly_print.raster import svg_to_jpeg, svg_to_png, svg_to_webp, write_raster


def _extract_figure_spec(fig: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if hasattr(fig, 'to_dict'):
        d = fig.to_dict()
    elif isinstance(fig, dict):
        d = fig
    else:
        raise TypeError(f'Expected plotly.graph_objects.Figure or dict, got {type(fig).__name__}')

    return d.get('data', []), d.get('layout', {})


def to_svg(
    fig: Any,
    width: int | None = None,
    height: int | None = None,
) -> str:
    data, layout = _extract_figure_spec(fig)
    return get_engine().render_svg(data, layout, width=width, height=height)


def to_image(
    fig: Any,
    format: str = 'png',
    width: int | None = None,
    height: int | None = None,
    scale: float = 1.0,
) -> bytes:
    fmt = format.lower().strip()
    svg = to_svg(fig, width=width, height=height)

    if fmt == 'svg':
        return svg.encode('utf-8')
    if fmt == 'png':
        return svg_to_png(svg, width=width, height=height, scale=scale)
    if fmt in ('jpg', 'jpeg'):
        return svg_to_jpeg(svg, width=width, height=height, scale=scale)
    if fmt == 'webp':
        return svg_to_webp(svg, width=width, height=height, scale=scale)
    raise ValueError(f"Unsupported format: {format}. Supported: 'svg', 'png', 'jpeg', 'webp'")


def write_image(
    fig: Any,
    file: str | os.PathLike[str] | BinaryIO,
    format: str | None = None,
    scale: float = 1.0,
    width: int | None = None,
    height: int | None = None,
) -> None:
    if format is None:
        if isinstance(file, (str, os.PathLike)):
            ext = os.path.splitext(str(file))[1].lower().lstrip('.')
            format = ext or 'png'
        else:
            format = 'png'

    fmt = format.lower().strip()
    svg_str = to_svg(fig, width=width, height=height)
    if fmt == 'svg':
        if isinstance(file, (str, os.PathLike)):
            with open(file, 'w', encoding='utf-8') as f:
                f.write(svg_str)
        else:
            file.write(svg_str.encode('utf-8'))
        return

    write_raster(svg_str, file, format=fmt, width=width, height=height, scale=scale)
