from __future__ import annotations

import argparse
import importlib.util
import statistics
import time
from io import BytesIO
from pathlib import Path

import plotly.graph_objects as go
from PIL import Image, ImageChops

import plotly_print
from benchmark.cases import CHARTS
from benchmark.collage import build_side_by_side
from benchmark.report import write_report

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / '.artifacts' / 'benchmark'

QUICK_KEYS = (
    'scatter_line',
    'bar',
    'pie',
    'box',
    'violin',
    'histogram',
    'heatmap',
    'rotated_ticks_45',
    'rotated_ticks_90',
)


def _kaleido_available() -> bool:
    return importlib.util.find_spec('kaleido') is not None


def _pixel_diff_max(print_bytes: bytes, kaleido_bytes: bytes) -> float | None:
    img_a = Image.open(BytesIO(print_bytes)).convert('RGB')
    img_b = Image.open(BytesIO(kaleido_bytes)).convert('RGB')
    if img_a.size != img_b.size:
        return None
    diff = ImageChops.difference(img_a, img_b)
    return float(max(channel[1] for channel in diff.getextrema()))


def _benchmark_png(render_fn, fig: go.Figure, rounds: int) -> tuple[bytes, float]:
    times: list[float] = []
    png: bytes = b''
    for _ in range(rounds):
        t0 = time.perf_counter()
        png = render_fn(fig)
        times.append(time.perf_counter() - t0)
    return png, statistics.mean(times)


def run_benchmark(*, output_dir: Path, quick: bool, rounds: int) -> int:
    if not _kaleido_available():
        print('kaleido is not installed. Sync the benchmark group: uv sync --group benchmark')
        return 1

    import kaleido  # noqa: F401

    keys = [k for k in QUICK_KEYS if k in CHARTS] if quick else list(CHARTS.keys())
    output_dir.mkdir(parents=True, exist_ok=True)

    dummy = go.Figure(data=[go.Scatter(x=[1], y=[1])])
    plotly_print.to_image(dummy, format='png')
    dummy.to_image(format='png')

    results: list[dict[str, object]] = []
    print(
        f'{"Category":<22} | {"Chart Type":<26} | {"plotly-print":<12} | {"Kaleido":<11} | {"Speedup":<8} | {"Px max"}'
    )
    print('-' * 95)

    for key in keys:
        info = CHARTS[key]
        category = info['category']
        title = info['title']
        fig = info['fig']

        png_print, avg_print = _benchmark_png(lambda f: plotly_print.to_image(f, format='png'), fig, rounds)
        png_kaleido, avg_kaleido = _benchmark_png(lambda f: f.to_image(format='png'), fig, rounds)

        speedup = avg_kaleido / avg_print if avg_print > 0 else 0.0
        px_max = _pixel_diff_max(png_print, png_kaleido)
        px_label = f'{px_max:.0f}' if px_max is not None else 'size mismatch'

        print(
            f'{category:<22} | {title:<26} | {avg_print * 1000:>9.1f} ms | '
            f'{avg_kaleido * 1000:>9.1f} ms | {speedup:>6.1f}x | {px_label}'
        )

        compare_name = f'compare_{key}.png'
        compare_path = output_dir / compare_name
        build_side_by_side(
            png_print,
            png_kaleido,
            'plotly-print (QuickJS)',
            'Kaleido (Chromium)',
            avg_print,
            avg_kaleido,
            compare_path,
        )
        (output_dir / f'{key}_plotly_print.png').write_bytes(png_print)
        (output_dir / f'{key}_kaleido.png').write_bytes(png_kaleido)

        results.append(
            {
                'key': key,
                'category': category,
                'title': title,
                'plotly_print_ms': round(avg_print * 1000, 1),
                'kaleido_ms': round(avg_kaleido * 1000, 1),
                'speedup': round(speedup, 2),
                'pixel_diff_max': px_max,
                'compare_image': compare_name,
            }
        )

    report_path = write_report(output_dir, results)
    print(f'\nWrote {len(results)} comparisons to {output_dir}')
    print(f'Report: {report_path}')
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description='Visual and timing benchmark: plotly-print vs Kaleido.')
    parser.add_argument(
        '--output',
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f'Output directory (default: {DEFAULT_OUTPUT})',
    )
    parser.add_argument('--quick', action='store_true', help='Run core cartesian charts plus rotated tick cases.')
    parser.add_argument('--rounds', type=int, default=3, help='Timing rounds per chart (default: 3).')
    args = parser.parse_args()
    raise SystemExit(run_benchmark(output_dir=args.output.resolve(), quick=args.quick, rounds=args.rounds))
