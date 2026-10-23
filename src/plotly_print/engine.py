from __future__ import annotations

import base64
import io
import json
import re
import struct
import threading
from pathlib import Path
from typing import Any

import quickjs
from PIL import Image, ImageColor, ImageDraw
from plotly.utils import PlotlyJSONEncoder

from plotly_print.fonts import get_default_font_manager

_JS_DIR = Path(__file__).resolve().parent / 'js'
_MICRO_DOM_PATH = _JS_DIR / 'micro_dom.js'
# Comprehensive 2D build: full plotly.min.js from the plotly package does not load in QuickJS.
_PLOTLY_JS_PATH = _JS_DIR / 'plotly_comprehensive_2d.js'

_ENGINE_THREAD_LOCAL = threading.local()


def _parse_color(c: str) -> tuple[int, int, int, int] | tuple[int, int, int]:
    if not c:
        return (0, 0, 0, 0)
    c = c.strip()
    m = re.match(r'rgba?\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)', c, re.I)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = int(float(m.group(4)) * 255) if m.group(4) is not None else 255
        return (r, g, b, a)
    try:
        return ImageColor.getrgb(c)
    except Exception:
        return (0, 0, 0, 255)


def _encode_canvas_to_png(width: int, height: int, commands_json: str) -> str:
    w = max(1, int(width))
    h = max(1, int(height))
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        commands = json.loads(commands_json)
    except Exception:
        commands = []

    for cmd in commands:
        op = cmd.get('op')
        if op == 'fillRect':
            x = cmd.get('x', 0)
            y = cmd.get('y', 0)
            cw = cmd.get('w', 0)
            ch = cmd.get('h', 0)
            fill = _parse_color(cmd.get('fill', '#000000'))
            draw.rectangle([x, y, x + cw, y + ch], fill=fill)
        elif op == 'clearRect':
            x = cmd.get('x', 0)
            y = cmd.get('y', 0)
            cw = cmd.get('w', 0)
            ch = cmd.get('h', 0)
            draw.rectangle([x, y, x + cw, y + ch], fill=(0, 0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/png;base64,{b64}'


# QuickJS throws on the out-of-bounds Uint8Array write plotly.js uses to drop
# base64 padding when decoding {'dtype', 'bdata'}. Expand those specs to lists
# before they reach the engine. Bytes are little-endian, matching the typed
# arrays plotly.js builds on the hosts this package runs on.
_TYPED_ARRAY_DTYPES = {
    'i1': 'b',
    'u1': 'B',
    'i2': 'h',
    'u2': 'H',
    'i4': 'i',
    'u4': 'I',
    'f4': 'f',
    'f8': 'd',
}


def _decode_typed_array(spec: dict[str, Any]) -> list[Any] | None:
    dtype = spec.get('dtype')
    bdata = spec.get('bdata')
    if not isinstance(dtype, str) or not isinstance(bdata, str):
        return None
    code = _TYPED_ARRAY_DTYPES.get(dtype)
    if code is None:
        return None
    shape = spec.get('shape')
    if 'shape' in spec and not isinstance(shape, (str, int)):
        return None

    raw = base64.b64decode(bdata)
    width = struct.calcsize(code)
    if len(raw) % width:
        raise ValueError(f'typed array byte length {len(raw)} is not a multiple of {width} for dtype {dtype}')
    flat = list(struct.unpack(f'<{len(raw) // width}{code}', raw))
    if shape is None:
        return flat
    dims = [int(part) for part in str(shape).split(',') if part.strip()]
    return _reshape_row_major(flat, dims)


def _reshape_row_major(flat: list[Any], dims: list[int]) -> list[Any]:
    size = 1
    for dim in dims:
        size *= dim
    if size != len(flat):
        joined = ','.join(str(dim) for dim in dims)
        raise ValueError(f'typed array shape {joined} does not match {len(flat)} values')
    if len(dims) <= 1:
        return flat
    span = size // dims[0]
    return [_reshape_row_major(flat[index * span : (index + 1) * span], dims[1:]) for index in range(dims[0])]


def _expand_typed_arrays(value: Any) -> Any:
    if isinstance(value, dict):
        decoded = _decode_typed_array(value)
        if decoded is not None:
            return decoded
        return {key: _expand_typed_arrays(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_expand_typed_arrays(item) for item in value]
    return value


class PrintEngine:
    def __init__(self) -> None:
        self.font_manager = get_default_font_manager()
        self.context = quickjs.Context()
        self.context.set_max_stack_size(10 * 1024 * 1024)

        self.context.add_callable('_measureTextRaw', self.font_manager.measure_raw)
        self.context.add_callable('_encodeCanvasToPNG', _encode_canvas_to_png)

        if not _PLOTLY_JS_PATH.is_file():
            raise FileNotFoundError(f'plotly.js bundle not found at {_PLOTLY_JS_PATH}')

        self.context.eval(_MICRO_DOM_PATH.read_text(encoding='utf-8'))
        self.context.eval(_PLOTLY_JS_PATH.read_text(encoding='utf-8'))

        self.context.eval("""
        function plotlyPrintRender(dataJson, layoutJson) {
            var data = JSON.parse(dataJson);
            var layout = JSON.parse(layoutJson);

            var w = layout.width || 600;
            var h = layout.height || 400;

            var container = document.createElement('div');
            container.id = 'plotly-print-' + Math.random().toString(36).slice(2);
            container.clientWidth = w;
            container.clientHeight = h;
            container.offsetWidth = w;
            container.offsetHeight = h;
            container.getBoundingClientRect = function() {
                return { left: 0, top: 0, right: w, bottom: h, width: w, height: h };
            };
            document.body.appendChild(container);

            try {
                Plotly.newPlot(container, data, layout, { staticPlot: true });
                var res = null;
                if (Plotly.Snapshot && typeof Plotly.Snapshot.toSVG === 'function') {
                    try {
                        res = Plotly.Snapshot.toSVG(container, 'svg');
                    } catch(snapErr) {
                    }
                }
                if (!res) {
                    var svgs = container.querySelectorAll('svg');
                    if (svgs.length === 0) {
                        document.body.removeChild(container);
                        return null;
                    }
                    var mainSvg = svgs[0];
                    for (var s = 1; s < svgs.length; s++) {
                        var otherSvg = svgs[s];
                        var kids = otherSvg.childNodes.slice();
                        for (var k = 0; k < kids.length; k++) {
                            var kid = kids[k];
                            if (kid.nodeType === 1 && kid.classList && kid.classList.contains('hoverlayer')) continue;
                            mainSvg.appendChild(kid);
                        }
                    }
                    res = mainSvg.outerHTML;
                }
                if (res) {
                    res = res.replace(/TOBESTRIPPED/g, "'");
                }
                document.body.removeChild(container);
                return res;
            } catch(e) {
                try { document.body.removeChild(container); } catch(ignore) {}
                throw new Error("Plotly render failed: " + e.message + "\\n" + e.stack);
            }
        }
        """)

    def render_svg(
        self,
        data: list[dict[str, Any]],
        layout: dict[str, Any],
        width: int | None = None,
        height: int | None = None,
    ) -> str:
        layout_copy = dict(layout) if layout else {}
        if width is not None:
            layout_copy['width'] = width
        if height is not None:
            layout_copy['height'] = height

        data_json = json.dumps(_expand_typed_arrays(data), cls=PlotlyJSONEncoder)
        layout_json = json.dumps(_expand_typed_arrays(layout_copy), cls=PlotlyJSONEncoder)

        self.context.eval(f'var __plotly_print_data = {json.dumps(data_json)};')
        self.context.eval(f'var __plotly_print_layout = {json.dumps(layout_json)};')
        svg = self.context.eval('plotlyPrintRender(__plotly_print_data, __plotly_print_layout);')
        if not svg:
            raise RuntimeError('plotly-print rendering failed: No SVG element was generated by Plotly.')
        return svg


def get_engine() -> PrintEngine:
    if not hasattr(_ENGINE_THREAD_LOCAL, 'engine'):
        _ENGINE_THREAD_LOCAL.engine = PrintEngine()
    return _ENGINE_THREAD_LOCAL.engine
