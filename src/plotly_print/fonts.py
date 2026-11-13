from __future__ import annotations

import os
import re
from collections.abc import Iterable
from pathlib import Path

from PIL import ImageFont

type FontPaths = Iterable[str | os.PathLike[str]] | str | os.PathLike[str]

FONT_SUFFIXES = ('.ttf', '.otf', '.ttc', '.otc')

_FONT_DIR = Path(__file__).resolve().parent / '_fonts'
BUNDLED_FONTS = sorted(
    (str(path) for path in _FONT_DIR.glob('*.ttf')),
    key=lambda path: ('bold' in Path(path).stem.lower(), path),
)


def _as_paths(paths: FontPaths | None) -> list[Path]:
    if paths is None:
        return []
    if isinstance(paths, (str, os.PathLike)):
        paths = [paths]
    return [Path(path) for path in paths]


def resolve_font_files(font_files: FontPaths | None = None) -> list[str]:
    paths = _as_paths(font_files)
    for path in paths:
        if not path.is_file():
            raise FileNotFoundError(f'Font file not found: {path}')
        try:
            ImageFont.truetype(str(path), 12)
        except OSError as exc:
            raise ValueError(f'Unsupported font file: {path}') from exc
    return [str(path) for path in paths]


def resolve_font_dirs(font_dirs: FontPaths | None = None) -> list[str]:
    paths = _as_paths(font_dirs)
    for path in paths:
        if not path.is_dir():
            raise NotADirectoryError(f'Font directory not found: {path}')
    return [str(path) for path in paths]


def expand_font_dirs(font_dirs: FontPaths | None = None) -> list[str]:
    return sorted(
        str(path)
        for directory in resolve_font_dirs(font_dirs)
        for path in Path(directory).rglob('*')
        if path.is_file() and path.suffix.lower() in FONT_SUFFIXES
    )


CANDIDATE_FONTS = [
    '/System/Library/Fonts/Supplemental/Arial.ttf',
    '/System/Library/Fonts/Helvetica.ttc',
    '/Library/Fonts/Arial.ttf',
    '/System/Library/Fonts/SFNSText.ttf',
    '/System/Library/Fonts/Supplemental/Verdana.ttf',
    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
    '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    'C:\\Windows\\Fonts\\arial.ttf',
    'C:\\Windows\\Fonts\\segoeui.ttf',
]


def _font_key(name: str) -> str:
    return re.sub(r'[^a-z0-9]', '', name.lower())


class FontManager:
    def __init__(self, font_files: FontPaths | None = None, font_dirs: FontPaths | None = None) -> None:
        self._font_cache: dict[tuple[str, int, str], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}
        self._measurement_cache: dict[tuple[str, str, int, str], tuple[float, float, float, float]] = {}
        system_fonts = [path for path in CANDIDATE_FONTS if Path(path).exists()]
        explicit_fonts = resolve_font_files(font_files)
        custom_fonts = list(dict.fromkeys(explicit_fonts + expand_font_dirs(font_dirs)))
        self._font_paths = system_fonts + BUNDLED_FONTS + custom_fonts
        self._default_font_path = system_fonts[0] if system_fonts else BUNDLED_FONTS[0] if BUNDLED_FONTS else None
        self._custom_font_families: dict[str, str] = {}
        for path in sorted(explicit_fonts, key=lambda item: ('bold' in Path(item).stem.lower(), item)):
            family = ImageFont.truetype(path, 12).getname()[0]
            self._custom_font_families.setdefault(_font_key(family), path)

    def get_font(self, family: str, size: float, weight: str = '') -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        int_size = max(1, round(size))
        cache_key = (family.lower().strip(), int_size, weight.lower().strip())
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font = None
        names = [r.strip().strip('"\'').lower() for r in family.split(',')]
        # Prefer Arial/Helvetica when Plotly's default stack lists verdana with sans-serif.
        if 'verdana' in names and ('arial' in names or 'sans-serif' in names or 'open sans' in names):
            names.remove('verdana')
            names.append('verdana')

        for clean_name in names:
            if not clean_name or clean_name in ('sans-serif', 'serif', 'monospace'):
                continue

            custom_font = self._custom_font_families.get(_font_key(clean_name))
            if custom_font:
                font = ImageFont.truetype(custom_font, size=int_size)
                break

            for test_name in (clean_name.title(), clean_name.capitalize(), clean_name):
                try:
                    font = ImageFont.truetype(test_name, size=int_size)
                    if font:
                        break
                except Exception:
                    pass
            if font:
                break

            target = _font_key(clean_name)
            for font_path in self._font_paths:
                if target and _font_key(Path(font_path).stem).startswith(target):
                    try:
                        font = ImageFont.truetype(font_path, size=int_size)
                        if font:
                            break
                    except Exception:
                        pass
            if font:
                break

        if font is None and self._default_font_path:
            try:
                font = ImageFont.truetype(self._default_font_path, size=int_size)
            except Exception:
                pass

        if font is None:
            try:
                font = ImageFont.load_default(size=int_size)
            except TypeError:
                font = ImageFont.load_default()

        self._font_cache[cache_key] = font
        return font

    def measure(self, text: str, family: str, size: float, weight: str = '') -> tuple[float, float, float, float]:
        int_size = max(1, round(size))
        cache_key = (text, family.lower().strip(), int_size, weight.lower().strip())
        if cache_key in self._measurement_cache:
            return self._measurement_cache[cache_key]

        if not text:
            res = (0.0, float(int_size), float(int_size), 0.0)
            self._measurement_cache[cache_key] = res
            return res

        font = self.get_font(family, size, weight)
        try:
            length = float(font.getlength(text))
        except Exception:
            length = float(len(text) * int_size * 0.6)

        try:
            bbox = font.getbbox(text)
            try:
                metrics = font.getmetrics()
                ascent_val = float(metrics[0])
                descent_val = float(metrics[1])
                h = max(ascent_val + descent_val, float(int_size * 1.2))
                ascent = ascent_val if ascent_val > 0 else float(int_size * 0.8)
                descent = descent_val if descent_val > 0 else float(int_size * 0.2)
            except Exception:
                h = float(int_size * 1.2)
                ascent = float(int_size * 0.8)
                descent = float(int_size * 0.2)

            if bbox:
                w = max(length, float(bbox[2] - bbox[0]))
            else:
                w = length
        except Exception:
            w, h = length, float(int_size * 1.2)
            ascent, descent = float(int_size * 0.8), float(int_size * 0.2)

        res = (round(w, 2), round(h, 2), round(ascent, 2), round(descent, 2))
        self._measurement_cache[cache_key] = res
        return res

    def measure_raw(self, text: str, family: str, size_str: str, weight: str = '') -> str:
        try:
            size = float(size_str)
        except (ValueError, TypeError):
            size = 12.0
        w, h, a, d = self.measure(text, family, size, weight)
        return f'{w},{h},{a},{d}'


_DEFAULT_FONT_MANAGER = FontManager()


def get_default_font_manager() -> FontManager:
    return _DEFAULT_FONT_MANAGER
