from __future__ import annotations

from typing import Any, BinaryIO

import plotly_print.core as core

_ORIGINAL_TO_IMAGE = None
_ORIGINAL_WRITE_IMAGE = None
_IS_PATCHED = False


def _patched_to_image(
    fig: Any,
    format: str | None = None,
    width: int | None = None,
    height: int | None = None,
    scale: float | None = None,
    validate: bool = True,
    **kwargs: Any,
) -> bytes:
    return core.to_image(
        fig,
        format=format or 'png',
        width=width,
        height=height,
        scale=scale or 1.0,
    )


def _patched_write_image(
    fig: Any,
    file: str | BinaryIO,
    format: str | None = None,
    scale: float | None = None,
    width: int | None = None,
    height: int | None = None,
    validate: bool = True,
    **kwargs: Any,
) -> None:
    core.write_image(
        fig,
        file=file,
        format=format,
        scale=scale or 1.0,
        width=width,
        height=height,
    )


def register() -> None:
    global _ORIGINAL_TO_IMAGE, _ORIGINAL_WRITE_IMAGE, _IS_PATCHED
    if _IS_PATCHED:
        return

    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        _ORIGINAL_TO_IMAGE = pio.to_image
        _ORIGINAL_WRITE_IMAGE = pio.write_image

        pio.to_image = _patched_to_image
        pio.write_image = _patched_write_image
        go.Figure.to_image = _patched_to_image
        go.Figure.write_image = _patched_write_image

        _IS_PATCHED = True
    except ImportError:
        pass


def unregister() -> None:
    global _ORIGINAL_TO_IMAGE, _ORIGINAL_WRITE_IMAGE, _IS_PATCHED
    if not _IS_PATCHED:
        return

    try:
        import plotly.graph_objects as go
        import plotly.io as pio

        if _ORIGINAL_TO_IMAGE:
            pio.to_image = _ORIGINAL_TO_IMAGE
            go.Figure.to_image = _ORIGINAL_TO_IMAGE

        if _ORIGINAL_WRITE_IMAGE:
            pio.write_image = _ORIGINAL_WRITE_IMAGE
            go.Figure.write_image = _ORIGINAL_WRITE_IMAGE

        _IS_PATCHED = False
    except ImportError:
        pass


patch_plotly = register
unpatch_plotly = unregister
