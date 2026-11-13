from __future__ import annotations

import bisect
import logging
import os
import re
import struct
import unicodedata
from collections.abc import Iterable
from functools import lru_cache
from pathlib import Path
from typing import NamedTuple

from PIL import ImageFont

type FontPaths = Iterable[str | os.PathLike[str]] | str | os.PathLike[str]

FONT_SUFFIXES = ('.ttf', '.otf', '.ttc', '.otc')

SYSTEM_FONT_DIRS = [
    '/System/Library/Fonts/Supplemental',
    '/Library/Fonts',
    '/System/Library/Fonts',
    '/usr/share/fonts',
    '/usr/local/share/fonts',
    'C:\\Windows\\Fonts',
]

_LOGGER = logging.getLogger(__name__)
_WARNED_MISSING_FONTS: set[str] = set()

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


@lru_cache(maxsize=1)
def _system_font_files() -> tuple[str, ...]:
    return tuple(
        str(path)
        for directory in SYSTEM_FONT_DIRS
        for path in sorted(Path(directory).rglob('*'))
        if path.is_file() and path.suffix.lower() in FONT_SUFFIXES
    )


@lru_cache(maxsize=8)
def _resolve_candidates(candidates: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    resolved: list[str] = []
    for path in candidates:
        if not Path(path).is_file():
            continue
        value = str(Path(path).resolve())
        if value not in seen:
            seen.add(value)
            resolved.append(value)
    return tuple(resolved)


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


def _codepoint_name(codepoint: int) -> str:
    char = chr(codepoint)
    return f'U+{codepoint:04X} ({char!r})' if char.isprintable() else f'U+{codepoint:04X}'


def _is_ignorable(char: str) -> bool:
    codepoint = ord(char)
    return (
        unicodedata.category(char) in ('Cc', 'Cf') or 0xFE00 <= codepoint <= 0xFE0F or 0xE0100 <= codepoint <= 0xE01EF
    )


class _FontFace(NamedTuple):
    family: str
    weight: int
    style: str
    path: str


def _u16(data: bytes, offset: int) -> int | None:
    if offset < 0 or offset + 2 > len(data):
        return None
    return struct.unpack_from('>H', data, offset)[0]


def _u32(data: bytes, offset: int) -> int | None:
    if offset < 0 or offset + 4 > len(data):
        return None
    return struct.unpack_from('>I', data, offset)[0]


def _font_tables(data: bytes) -> dict[bytes, tuple[int, int]]:
    offset = 0
    if data[:4] == b'ttcf':
        offset = _u32(data, 12) or 0
        if not offset:
            return {}

    num_tables = _u16(data, offset + 4)
    if num_tables is None:
        return {}

    tables: dict[bytes, tuple[int, int]] = {}
    for index in range(num_tables):
        record = offset + 12 + index * 16
        if record + 16 > len(data):
            break
        table_offset = _u32(data, record + 8)
        table_length = _u32(data, record + 12)
        if table_offset is not None and table_length is not None:
            tables[data[record : record + 4]] = (table_offset, table_length)
    return tables


def _read_font_weight(path: str) -> int | None:
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    table = _font_tables(data).get(b'OS/2')
    if table is None:
        return None
    weight = _u16(data, table[0] + 4)
    return weight if weight is not None and 1 <= weight <= 1000 else None


class _Cmap:
    __slots__ = ('_ranges', '_starts')

    def __init__(self, ranges: list[tuple[int, int]]) -> None:
        merged: list[tuple[int, int]] = []
        for start, end in sorted(ranges):
            if start > end:
                continue
            if merged and start <= merged[-1][1] + 1:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        self._ranges = merged
        self._starts = [start for start, _ in merged]

    def covers(self, codepoint: int) -> bool:
        index = bisect.bisect_right(self._starts, codepoint) - 1
        return index >= 0 and codepoint <= self._ranges[index][1]


def _cmap_format_0(data: bytes, table: int) -> list[tuple[int, int]] | None:
    if table + 6 + 256 > len(data):
        return None
    return [(index, index) for index, glyph in enumerate(data[table + 6 : table + 6 + 256]) if glyph]


def _cmap_format_4(data: bytes, table: int) -> list[tuple[int, int]] | None:
    seg_count_x2 = _u16(data, table + 6)
    if not seg_count_x2 or seg_count_x2 % 2:
        return None
    seg_count = seg_count_x2 // 2
    ends = table + 14
    starts = ends + seg_count * 2 + 2
    deltas = starts + seg_count * 2
    offsets = deltas + seg_count * 2
    glyphs = offsets + seg_count * 2
    if glyphs > len(data):
        return None

    ranges: list[tuple[int, int]] = []
    for segment in range(seg_count):
        end = _u16(data, ends + segment * 2)
        start = _u16(data, starts + segment * 2)
        delta = _u16(data, deltas + segment * 2)
        offset = _u16(data, offsets + segment * 2)
        if None in (start, end, delta, offset):
            return None
        if start == 0xFFFF:
            continue

        run_start: int | None = None
        previous = start
        for codepoint in range(start, end + 1):
            if offset == 0:
                glyph = (codepoint + delta) & 0xFFFF
            else:
                glyph = _u16(data, offsets + segment * 2 + offset + (codepoint - start) * 2)
                if glyph:
                    glyph = (glyph + delta) & 0xFFFF
            if glyph:
                if run_start is None:
                    run_start = codepoint
                previous = codepoint
            elif run_start is not None:
                ranges.append((run_start, previous))
                run_start = None
        if run_start is not None:
            ranges.append((run_start, previous))
    return ranges


def _cmap_format_6(data: bytes, table: int) -> list[tuple[int, int]] | None:
    first = _u16(data, table + 6)
    count = _u16(data, table + 8)
    if first is None or count is None or table + 10 + count * 2 > len(data):
        return None
    return [(first + index, first + index) for index in range(count) if _u16(data, table + 10 + index * 2)]


def _cmap_format_10(data: bytes, table: int) -> list[tuple[int, int]] | None:
    first = _u32(data, table + 12)
    count = _u32(data, table + 16)
    if first is None or count is None or table + 20 + count * 2 > len(data):
        return None
    return [(first + index, first + index) for index in range(count) if _u16(data, table + 20 + index * 2)]


def _cmap_format_12(data: bytes, table: int, *, constant: bool = False) -> list[tuple[int, int]] | None:
    count = _u32(data, table + 12)
    if count is None or table + 16 + count * 12 > len(data):
        return None
    ranges: list[tuple[int, int]] = []
    for index in range(count):
        record = table + 16 + index * 12
        start = _u32(data, record)
        end = _u32(data, record + 4)
        glyph = _u32(data, record + 8)
        if None in (start, end, glyph) or start > end:
            continue
        if glyph:
            ranges.append((start, end))
        elif not constant and end > start:
            ranges.append((start + 1, end))
    return ranges


def _cmap_format_13(data: bytes, table: int) -> list[tuple[int, int]] | None:
    return _cmap_format_12(data, table, constant=True)


_CMAP_FORMATS = {
    0: _cmap_format_0,
    4: _cmap_format_4,
    6: _cmap_format_6,
    10: _cmap_format_10,
    12: _cmap_format_12,
    13: _cmap_format_13,
}
_CMAP_FORMAT_SCORE = {0: 1, 4: 3, 6: 2, 10: 3, 12: 5, 13: 4}


def _cmap_platform_score(platform: int, encoding: int) -> int:
    if platform == 0:
        return 2
    if platform == 3 and encoding == 10:
        return 2
    if platform == 3 and encoding == 1:
        return 1
    return -1


# Coverage decides which fallback font resvg will use; parse cmap directly to avoid a fontTools dependency.
@lru_cache(maxsize=256)
def _font_cmap(path: str) -> _Cmap | None:
    try:
        data = Path(path).read_bytes()
    except OSError:
        return None
    table = _font_tables(data).get(b'cmap')
    if table is None:
        return None
    base = table[0]
    if _u16(data, base) != 0:
        return None
    count = _u16(data, base + 2)
    if count is None:
        return None

    best_score = -1
    best_ranges: list[tuple[int, int]] | None = None
    for index in range(count):
        record = base + 4 + index * 8
        if record + 8 > len(data):
            break
        platform, encoding = struct.unpack_from('>HH', data, record)
        platform_score = _cmap_platform_score(platform, encoding)
        subtable_offset = _u32(data, record + 4)
        if platform_score < 0 or subtable_offset is None:
            continue
        subtable = base + subtable_offset
        fmt = _u16(data, subtable)
        parser = _CMAP_FORMATS.get(fmt)
        if parser is None:
            continue
        score = _CMAP_FORMAT_SCORE[fmt] * 10 + platform_score
        if score <= best_score:
            continue
        ranges = parser(data, subtable)
        if ranges is None:
            continue
        best_score = score
        best_ranges = ranges
    return _Cmap(best_ranges) if best_ranges is not None else None


def _style_weight(style: str) -> int | None:
    value = _font_key(style)
    for token, weight in (
        ('thin', 100),
        ('extralight', 200),
        ('ultralight', 200),
        ('semibold', 600),
        ('demibold', 600),
        ('extrabold', 800),
        ('ultrabold', 800),
        ('light', 300),
        ('medium', 500),
        ('bold', 700),
        ('black', 900),
        ('heavy', 900),
    ):
        if token in value:
            return weight
    return None


def _font_face_weight(path: str, style: str) -> int:
    weight = _read_font_weight(path)
    style_weight = _style_weight(style)
    if weight is None:
        return style_weight or 400
    if style_weight is not None and (weight == 400 or abs(weight - style_weight) >= 200):
        return style_weight
    return weight


def _weight_value(weight: str) -> int:
    value = weight.strip().lower()
    try:
        return max(1, min(1000, round(float(value))))
    except ValueError:
        pass
    return {
        'thin': 100,
        'extralight': 200,
        'ultralight': 200,
        'light': 300,
        'lighter': 300,
        'normal': 400,
        'regular': 400,
        'book': 400,
        'medium': 500,
        'semibold': 600,
        'demibold': 600,
        'bold': 700,
        'bolder': 700,
        'extrabold': 800,
        'ultrabold': 800,
        'black': 900,
        'heavy': 900,
    }.get(value, 400)


class FontManager:
    def __init__(self, font_files: FontPaths | None = None, font_dirs: FontPaths | None = None) -> None:
        self._font_cache: dict[tuple[str, int, str], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}
        self._measurement_cache: dict[tuple[str, str, int, str], tuple[float, float, float, float]] = {}
        system_fonts = [path for path in CANDIDATE_FONTS if Path(path).exists()]
        explicit_fonts = resolve_font_files(font_files)
        self._explicit_fonts = explicit_fonts
        self._dir_fonts = expand_font_dirs(font_dirs)
        custom_fonts = list(dict.fromkeys(explicit_fonts + self._dir_fonts))
        self._font_paths = system_fonts + BUNDLED_FONTS + custom_fonts
        self._default_font_path = system_fonts[0] if system_fonts else BUNDLED_FONTS[0] if BUNDLED_FONTS else None
        self._custom_fonts: list[_FontFace] = []
        for path in explicit_fonts:
            family, style = ImageFont.truetype(path, 12).getname()
            self._custom_fonts.append(_FontFace(_font_key(family), _font_face_weight(path, style), style, path))
        self._fallback_paths: list[str] | None = None
        self._fallback_choices: dict[tuple[str, tuple[int, ...]], str | None] = {}
        self._fallback_fonts: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

    def _select_custom_font(self, family: str, weight: str) -> str | None:
        key = _font_key(family)
        faces = [
            face for face in self._custom_fonts if face.family == key or _font_key(Path(face.path).stem).startswith(key)
        ]
        if not faces:
            return None
        target = _weight_value(weight)
        return min(
            faces,
            key=lambda face: (abs(face.weight - target), face.weight, 'italic' in face.style.lower(), face.path),
        ).path

    def _fallback_candidates(self) -> list[str]:
        if self._fallback_paths is None:
            system = _resolve_candidates((*CANDIDATE_FONTS, *_system_font_files()))
            custom = _resolve_candidates((*self._explicit_fonts, *BUNDLED_FONTS, *self._dir_fonts))
            seen = set(system)
            self._fallback_paths = [*system, *(path for path in custom if path not in seen)]
        return self._fallback_paths

    def _find_fallback(self, primary_path: str, codepoints: set[int]) -> str | None:
        primary = str(Path(primary_path).resolve())
        for path in self._fallback_candidates():
            if path == primary:
                continue
            cmap = _font_cmap(path)
            if cmap is not None and all(cmap.covers(codepoint) for codepoint in codepoints):
                return path
        return None

    def _font_for_text(
        self, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, text: str, size: float
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        path = getattr(font, 'path', None)
        if not path or not text:
            return font
        cmap = _font_cmap(path)
        if cmap is None:
            return font

        codepoints = {ord(char) for char in text if not _is_ignorable(char)}
        missing = sorted(codepoint for codepoint in codepoints if not cmap.covers(codepoint))
        if not missing:
            return font

        key = (path, tuple(sorted(codepoints)))
        if key not in self._fallback_choices:
            self._fallback_choices[key] = self._find_fallback(path, codepoints)
        fallback_path = self._fallback_choices[key]

        if path not in _WARNED_MISSING_FONTS:
            _WARNED_MISSING_FONTS.add(path)
            names = ', '.join(_codepoint_name(codepoint) for codepoint in missing)
            _LOGGER.warning(
                'Font %s is missing %s; measuring with %s.',
                path,
                names,
                fallback_path or 'the original font',
            )

        if not fallback_path:
            return font
        int_size = max(1, round(size))
        font_key = (fallback_path, int_size)
        if font_key not in self._fallback_fonts:
            self._fallback_fonts[font_key] = ImageFont.truetype(fallback_path, int_size)
        return self._fallback_fonts[font_key]

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

            custom_font = self._select_custom_font(clean_name, weight)
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

        font = self._font_for_text(self.get_font(family, size, weight), text, size)
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
