import shutil
from pathlib import Path

import plotly.graph_objects as go
import pytest
from PIL import ImageFont

import plotly_print
from plotly_print import fonts, raster


def _svg(family: str) -> str:
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="60">'
        '<rect width="300" height="60" fill="white"/>'
        f'<text x="10" y="40" font-size="30" font-family="{family}">Wgjy</text></svg>'
    )


def test_bundled_font_is_dejavu_sans():
    regular = Path(fonts.BUNDLED_FONTS[0])
    assert regular.name == 'DejaVuSans.ttf'
    assert ImageFont.truetype(str(regular), 12).getname()[0] == 'DejaVu Sans'


def test_font_manager_falls_back_to_bundled_font(monkeypatch):
    monkeypatch.setattr(fonts, 'CANDIDATE_FONTS', [])
    manager = fonts.FontManager()
    assert manager.get_font('Plotly Print Missing Font', 12).getname()[0] == 'DejaVu Sans'


def test_raster_uses_bundled_font_when_no_system_fonts(monkeypatch):
    monkeypatch.setattr(raster, 'EXISTING_FONT_DIRS', [])
    monkeypatch.setattr(raster, '_SYSTEM_FONT_STEMS', set())

    options = raster._resvg_font_options()
    assert options['sans_serif_family'] == 'DejaVu Sans'
    assert options['serif_family'] == 'DejaVu Serif'
    assert options['monospace_family'] == 'DejaVu Sans Mono'
    assert options['font_family'] == 'DejaVu Sans'
    assert all(Path(path).is_file() for path in options['font_files'])


def test_raster_keeps_installed_generic_fonts(monkeypatch):
    monkeypatch.setattr(raster, 'EXISTING_FONT_DIRS', ['/usr/share/fonts'])
    monkeypatch.setattr(raster, '_SYSTEM_FONT_STEMS', {'arial', 'timesnewroman', 'couriernew'})

    options = raster._resvg_font_options()
    assert options['sans_serif_family'] == 'Arial'
    assert options['serif_family'] == 'Times New Roman'
    assert options['monospace_family'] == 'Courier New'
    assert 'font_family' not in options


def test_missing_family_renders_with_bundled_font(monkeypatch):
    monkeypatch.setattr(raster, 'EXISTING_FONT_DIRS', [])
    monkeypatch.setattr(raster, '_SYSTEM_FONT_STEMS', set())

    fallback = raster.svg_to_png(_svg('Plotly Print Missing Font, sans-serif'))
    explicit = raster.svg_to_png(_svg('DejaVu Sans'))
    assert fallback == explicit


def test_custom_font_file_is_used_for_metrics(tmp_path):
    custom = tmp_path / 'renamed.ttf'
    shutil.copy(fonts.BUNDLED_FONTS[0], custom)

    manager = fonts.FontManager(font_files=custom)
    assert Path(manager.get_font('DejaVu Sans', 12).path) == custom


def test_custom_font_dir_is_used_for_metrics(tmp_path):
    custom = tmp_path / 'customsans.ttf'
    shutil.copy(fonts.BUNDLED_FONTS[0], custom)

    manager = fonts.FontManager(font_dirs=tmp_path)
    assert Path(manager.get_font('Customsans', 12).path) == custom


def test_raster_includes_custom_font_sources(tmp_path):
    custom = tmp_path / 'custom.ttf'
    shutil.copy(fonts.BUNDLED_FONTS[0], custom)

    options = raster._resvg_font_options(font_files=[custom], font_dirs=[tmp_path])
    assert str(custom) in options['font_files']
    assert str(tmp_path) in options['font_dirs']


def test_invalid_font_sources_raise(tmp_path):
    with pytest.raises(FileNotFoundError):
        fonts.resolve_font_files(tmp_path / 'missing.ttf')
    with pytest.raises(NotADirectoryError):
        fonts.resolve_font_dirs(tmp_path / 'missing')

    invalid = tmp_path / 'invalid.ttf'
    invalid.write_text('not a font')
    with pytest.raises(ValueError):
        fonts.resolve_font_files(invalid)


def test_export_accepts_custom_font_sources(tmp_path):
    custom = tmp_path / 'DejaVuSans.ttf'
    shutil.copy(fonts.BUNDLED_FONTS[0], custom)
    fig = go.Figure(
        data=[go.Scatter(x=[1, 2], y=[3, 4])],
        layout=go.Layout(width=200, height=100, font={'family': 'DejaVu Sans'}),
    )

    assert plotly_print.to_image(fig, font_files=str(custom)).startswith(b'\x89PNG')
    assert plotly_print.to_image(fig, font_dirs=str(tmp_path)).startswith(b'\x89PNG')
    assert plotly_print.to_image(fig, font_files=iter([custom])).startswith(b'\x89PNG')
    assert plotly_print.to_svg(fig, font_dirs=iter([tmp_path])).startswith('<svg')
