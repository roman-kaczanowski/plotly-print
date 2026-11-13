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

## Fonts

`fonts.py` owns measurement; `raster.py` owns rendering. Keep the two paths aligned or labels will clip.

- **Public API:** `to_svg`, `to_image`, `write_image`, and patched Plotly methods accept `font_files` and `font_dirs`. Normalize inputs with `fonts.resolve_font_files` / `resolve_font_dirs`; supported suffixes live in `FONT_SUFFIXES`.
- **Resolution:** explicit files match by internal family name or filename stem and select a face by weight. Then `CANDIDATE_FONTS`, bundled `_fonts/`, and custom directories. `font_dirs` are scanned recursively.
- **Weights:** `FontManager.get_font` reads OS/2 `usWeightClass`, falls back to the style name, and normalizes requested CSS/numeric weights. Keep the closest-weight selection deterministic.
- **Coverage:** `measure` parses the selected face cmap (formats 0/4/6/10/12/13). Missing code points switch measurement to the first fallback in resvg load order: system fonts, explicit files, bundled, custom directories. One `logging` warning per font path names the missing code points.
- **Generic families:** `raster._BUNDLED_FALLBACKS` maps sans/serif/monospace to installed system families, then bundled DejaVu. Keep it consistent with `CANDIDATE_FONTS`.
- **No parser dependency:** OS/2 and cmap are parsed manually with `struct`; do not add `fonttools`.
- **Caches:** `_font_cmap`, `_system_font_files`, and `_resolve_candidates` are process-wide; fallback choices are per `FontManager`. Missing-glyph work is lazy; do not scan fonts at import.
- **Licensing:** bundled DejaVu files are covered by `_fonts/DejaVu-LICENSE.txt` and `THIRD_PARTY_NOTICES.md`; update both if the faces change.
- **Tests:** `tests/test_fonts.py`; run it for font changes, plus `tests/test_kaleido_visual.py` when metrics or rasterization change.

## Related context

- JS and micro-DOM: `js/AGENTS.md`.
- Tests: `../../tests/AGENTS.md`.
- Vendored bundle: opaque; never read or grep the whole file. Use capped shell `grep -o ... | head` for call shapes.
