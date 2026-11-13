# Package map

Browser-less Plotly static export: QuickJS + micro-DOM + vendored Plotly 2D -> SVG -> resvg raster.

## Flow

`core.to_svg` / `to_image` / `write_image` -> `engine.PrintEngine` (QuickJS) -> eval `micro_dom.js` + vendored Plotly -> SVG -> `raster.py` for png/jpeg/webp.

`plotly_hook.register` patches Plotly `to_image` / `write_image`.

## Files

| Path                            | Job                                             |
| ------------------------------- | ----------------------------------------------- |
| `core.py`                       | Public API; figure -> JSON                      |
| `engine.py`                     | QuickJS lifecycle; canvas -> PNG; typed arrays  |
| `fonts.py`                      | Text metrics callable into JS; font fallbacks   |
| `_fonts/`                       | Bundled DejaVu fallback fonts + license         |
| `raster.py`                     | SVG -> raster (resvg)                           |
| `plotly_hook.py`                | Monkeypatch Plotly                              |
| `js/micro_dom.js`               | First-party DOM/SVG stubs (**edit here**)       |
| `js/plotly_comprehensive_2d.js` | Vendored; **never** read or grep the whole file |

Start from this map. Open only listed files unless the task is outside `src/plotly_print/`.

## Related context

- JS and micro-DOM: `js/AGENTS.md`.
- Tests: `../../tests/AGENTS.md`.
- Vendored bundle: opaque; never read or grep the whole file. Use capped shell `grep -o ... | head` for call shapes.
