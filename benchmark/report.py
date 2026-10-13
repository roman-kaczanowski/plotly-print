from __future__ import annotations

import json
from pathlib import Path

BENCHMARK_START = '<!-- BENCHMARK-START -->'
BENCHMARK_END = '<!-- BENCHMARK-END -->'
RAW_BASE = 'https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks'


def _speedup_range(results: list[dict[str, object]]) -> tuple[float, float]:
    vals = [float(row['speedup']) for row in results if float(row['speedup']) > 0]
    if not vals:
        return 0.0, 0.0
    return min(vals), max(vals)


def build_readme_section(results: list[dict[str, object]]) -> str:
    n = len(results)
    lo, hi = _speedup_range(results)
    lines = [
        '## Benchmarks',
        '',
        f'On this run, plotly-print exported all {n} chart types **{lo:.0f}x to {hi:.0f}x faster** than Kaleido.',
        '',
        'These are mean per-image PNG export times after both engines were warmed up. Timings are machine-specific; '
        'use the side-by-side images below to evaluate rendering differences.',
        '',
        'See the [raw results](assets/benchmarks/benchmark_summary.json) or '
        '[run the benchmark locally](CONTRIBUTING.md#kaleido-visual-benchmark).',
        '',
        '| Category | Chart Type | Kaleido | plotly-print | Speedup |',
        '| :--- | :--- | :---: | :---: | :---: |',
    ]
    for row in results:
        lines.append(
            f'| **{row["category"]}** | {row["title"]} | '
            f'{row["kaleido_ms"]:.1f} ms | **{row["plotly_print_ms"]:.1f} ms** | '
            f'**{row["speedup"]:.1f}x** |'
        )
    lines.extend(
        [
            '',
            '## Visual comparisons',
            '',
            'Side-by-side PNGs (Kaleido left, plotly-print right):',
            '',
        ]
    )

    current_cat = None
    for row in results:
        cat = str(row['category'])
        if cat != current_cat:
            current_cat = cat
            lines.append(f'### {cat}')
            lines.append('')
        title = str(row['title'])
        key = str(row['key'])
        lines.append(
            f'#### {title} (plotly-print: {row["plotly_print_ms"]:.1f}ms | Kaleido: {row["kaleido_ms"]:.1f}ms)'
        )
        lines.append('')
        lines.append(f'![{title}]({RAW_BASE}/compare_{key}.png)')
        lines.append('')

    return '\n'.join(lines).rstrip() + '\n'


def update_readme(readme_path: Path, results: list[dict[str, object]]) -> None:
    section = build_readme_section(results)
    block = f'{BENCHMARK_START}\n{section}{BENCHMARK_END}'
    text = readme_path.read_text(encoding='utf-8') if readme_path.is_file() else ''

    if BENCHMARK_START in text and BENCHMARK_END in text:
        before, rest = text.split(BENCHMARK_START, 1)
        _, after = rest.split(BENCHMARK_END, 1)
        text = f'{before}{block}{after}'
    else:
        anchor = '\n## Attribution\n'
        if anchor in text:
            text = text.replace(anchor, f'\n{block}\n{anchor}', 1)
        else:
            text = text.rstrip() + '\n\n' + block + '\n'

    readme_path.write_text(text, encoding='utf-8')


def write_report(output_dir: Path, results: list[dict[str, object]], *, readme_path: Path | None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = output_dir / 'benchmark_summary.json'
    summary.write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    if readme_path is not None:
        update_readme(readme_path, results)
    return summary
