from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path


def write_report(output_dir: Path, results: list[dict[str, object]]) -> Path:
    generated = datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        '# plotly-print vs Kaleido',
        '',
        f'Generated {generated}.',
        '',
        '| Category | Chart | plotly-print (ms) | Kaleido (ms) | Speedup | Pixel diff max |',
        '| --- | --- | ---: | ---: | ---: | ---: |',
    ]
    for row in results:
        px = row['pixel_diff_max']
        px_cell = f'{px:.0f}' if px is not None else 'size mismatch'
        lines.append(
            f'| {row["category"]} | {row["title"]} | {row["plotly_print_ms"]} | '
            f'{row["kaleido_ms"]} | {row["speedup"]} | {px_cell} |'
        )
    lines.extend(['', '## Comparisons', ''])
    for row in results:
        lines.append(f'### {row["title"]}')
        lines.append('')
        lines.append(f'`{row["key"]}`')
        lines.append('')
        lines.append(f'![{row["title"]}]({row["compare_image"]})')
        lines.append('')

    summary = output_dir / 'benchmark_summary.json'
    summary.write_text(json.dumps(results, indent=2), encoding='utf-8')

    path = output_dir / 'report.md'
    path.write_text('\n'.join(lines), encoding='utf-8')
    return path
