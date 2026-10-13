# plotly-print

[![CI](https://img.shields.io/github/actions/workflow/status/roman-kaczanowski/plotly-print/quality-checks.yml?branch=main&style=flat-square&label=CI)](https://github.com/roman-kaczanowski/plotly-print/actions/workflows/quality-checks.yml) [![PyPI](https://img.shields.io/pypi/v/plotly-print?style=flat-square)](https://pypi.org/project/plotly-print/) [![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://docs.python.org/3/) [![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

Export Plotly figures to SVG, PNG, JPEG, or WebP without launching Chrome.

plotly-print runs a bundled Plotly.js 2D build in QuickJS, then uses `resvg-py` for raster output. It works offline, has no browser process to install or manage, and can replace Plotly's image-export methods with one call.

- Browser-free: no Chrome, Chromium, or Playwright.
- Fast: avoids browser startup; see the measured [benchmarks](#benchmarks).
- Familiar: use the direct API or patch Plotly's existing `to_image` and `write_image` methods.

[Install](#installation) | [Direct API](#direct-api) | [Plotly integration](#plotly-integration) | [Benchmarks](#benchmarks)

## Installation

```bash
pip install plotly-print
```

Requires Python 3.12 or newer.

## Direct API

```python
import plotly.express as px
import plotly_print

fig = px.scatter(x=[1, 2, 3, 4], y=[10, 11, 12, 13], title='Sales Growth')

svg = plotly_print.to_svg(fig)
png = plotly_print.to_image(fig, format='png', scale=2)
plotly_print.write_image(fig, 'chart.png')
```

`to_image` returns bytes. `write_image` writes to a path or binary file object. Supported formats are SVG, PNG, JPEG, and WebP.

## Plotly integration

Patch Plotly's existing image-export methods:

```python
import plotly_print

plotly_print.register()
```

After registration, existing calls such as `fig.write_image("chart.png")` use plotly-print. Call `plotly_print.unregister()` to restore Plotly's original methods.

plotly-print targets 2D static charts. The bundled Plotly.js build and its licenses are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

<!-- BENCHMARK-START -->

## Benchmarks

On this run, plotly-print exported all 29 chart types **11x to 84x faster** than Kaleido.

These are mean per-image PNG export times after both engines were warmed up. Timings are machine-specific; use the side-by-side images below to evaluate rendering differences.

See the [raw results](assets/benchmarks/benchmark_summary.json) or [run the benchmark locally](CONTRIBUTING.md#kaleido-visual-benchmark).

| Category                 | Chart Type                                |  Kaleido  | plotly-print |  Speedup  |
| :----------------------- | :---------------------------------------- | :-------: | :----------: | :-------: |
| **Core Cartesian**       | Scatter & Line Chart                      | 1732.3 ms | **99.5 ms**  | **17.4x** |
| **Core Cartesian**       | Grouped Bar Chart                         | 1662.3 ms | **95.9 ms**  | **17.3x** |
| **Core Cartesian**       | Donut / Pie Chart                         | 1664.5 ms | **74.7 ms**  | **22.3x** |
| **Core Cartesian**       | Box Plot                                  | 1893.0 ms | **93.1 ms**  | **20.3x** |
| **Core Cartesian**       | Violin Plot                               | 2504.6 ms | **99.2 ms**  | **25.2x** |
| **Core Cartesian**       | Frequency Histogram                       | 1695.0 ms | **78.6 ms**  | **21.6x** |
| **Core Cartesian**       | 2D Density Histogram                      | 2136.3 ms | **98.8 ms**  | **21.6x** |
| **Core Cartesian**       | 2D Contour Plot                           | 1630.0 ms | **132.2 ms** | **12.3x** |
| **Core Cartesian**       | Performance Heatmap                       | 6032.4 ms | **87.6 ms**  | **68.9x** |
| **Core Cartesian**       | Ternary Phase Diagram                     | 8172.7 ms | **97.9 ms**  | **83.5x** |
| **Financial & Business** | Candlestick Stock Chart                   | 1988.8 ms | **179.8 ms** | **11.1x** |
| **Financial & Business** | OHLC Financial Chart                      | 1814.0 ms | **131.4 ms** | **13.8x** |
| **Financial & Business** | Waterfall Profit & Loss                   | 1907.6 ms | **67.0 ms**  | **28.5x** |
| **Financial & Business** | Sales Conversion Funnel                   | 1914.4 ms | **104.0 ms** | **18.4x** |
| **Financial & Business** | Funnel Area Analysis                      | 1658.5 ms | **69.7 ms**  | **23.8x** |
| **Financial & Business** | KPI Performance Indicator                 | 1541.5 ms | **58.6 ms**  | **26.3x** |
| **Hierarchical**         | Market Cap Treemap                        | 1625.0 ms | **64.9 ms**  | **25.1x** |
| **Hierarchical**         | Global Sunburst Hierarchy                 | 1698.7 ms | **55.9 ms**  | **30.4x** |
| **Hierarchical**         | Icicle Partition Chart                    | 1517.1 ms | **59.2 ms**  | **25.6x** |
| **Radial & Polar**       | Radar Performance Comparison              | 1667.7 ms | **124.3 ms** | **13.4x** |
| **Radial & Polar**       | Polar Wind Rose                           | 1785.0 ms | **81.7 ms**  | **21.9x** |
| **Specialized Diagrams** | Energy Flow Sankey Diagram                | 1714.3 ms | **63.6 ms**  | **27.0x** |
| **Specialized Diagrams** | Parallel Categories Diagram               | 1661.2 ms | **66.5 ms**  | **25.0x** |
| **Specialized Diagrams** | Formatted Data Table                      | 1819.0 ms | **78.3 ms**  | **23.2x** |
| **Specialized Diagrams** | Carpet Coordinate Plot                    | 1710.2 ms | **119.2 ms** | **14.3x** |
| **Layout edge cases**    | Bar chart with X labels at 45 deg         | 1804.5 ms | **110.8 ms** | **16.3x** |
| **Layout edge cases**    | Bar chart with X labels at 90 deg         | 1886.6 ms | **127.6 ms** | **14.8x** |
| **Layout edge cases**    | Annotation arrowheads (incl. circle)      | 1657.9 ms | **101.9 ms** | **16.3x** |
| **Layout edge cases**    | Long annotation arrows (dasharray length) | 1803.9 ms | **98.6 ms**  | **18.3x** |

## Visual comparisons

Side-by-side PNGs (Kaleido left, plotly-print right):

### Core Cartesian

#### Scatter & Line Chart (plotly-print: 99.5ms | Kaleido: 1732.3ms)

![Scatter & Line Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatter_line.png)

#### Grouped Bar Chart (plotly-print: 95.9ms | Kaleido: 1662.3ms)

![Grouped Bar Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_bar.png)

#### Donut / Pie Chart (plotly-print: 74.7ms | Kaleido: 1664.5ms)

![Donut / Pie Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_pie.png)

#### Box Plot (plotly-print: 93.1ms | Kaleido: 1893.0ms)

![Box Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_box.png)

#### Violin Plot (plotly-print: 99.2ms | Kaleido: 2504.6ms)

![Violin Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_violin.png)

#### Frequency Histogram (plotly-print: 78.6ms | Kaleido: 1695.0ms)

![Frequency Histogram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_histogram.png)

#### 2D Density Histogram (plotly-print: 98.8ms | Kaleido: 2136.3ms)

![2D Density Histogram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_histogram2d.png)

#### 2D Contour Plot (plotly-print: 132.2ms | Kaleido: 1630.0ms)

![2D Contour Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_contour.png)

#### Performance Heatmap (plotly-print: 87.6ms | Kaleido: 6032.4ms)

![Performance Heatmap](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_heatmap.png)

#### Ternary Phase Diagram (plotly-print: 97.9ms | Kaleido: 8172.7ms)

![Ternary Phase Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatterternary.png)

### Financial & Business

#### Candlestick Stock Chart (plotly-print: 179.8ms | Kaleido: 1988.8ms)

![Candlestick Stock Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_candlestick.png)

#### OHLC Financial Chart (plotly-print: 131.4ms | Kaleido: 1814.0ms)

![OHLC Financial Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_ohlc.png)

#### Waterfall Profit & Loss (plotly-print: 67.0ms | Kaleido: 1907.6ms)

![Waterfall Profit & Loss](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_waterfall.png)

#### Sales Conversion Funnel (plotly-print: 104.0ms | Kaleido: 1914.4ms)

![Sales Conversion Funnel](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_funnel.png)

#### Funnel Area Analysis (plotly-print: 69.7ms | Kaleido: 1658.5ms)

![Funnel Area Analysis](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_funnelarea.png)

#### KPI Performance Indicator (plotly-print: 58.6ms | Kaleido: 1541.5ms)

![KPI Performance Indicator](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_indicator.png)

### Hierarchical

#### Market Cap Treemap (plotly-print: 64.9ms | Kaleido: 1625.0ms)

![Market Cap Treemap](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_treemap.png)

#### Global Sunburst Hierarchy (plotly-print: 55.9ms | Kaleido: 1698.7ms)

![Global Sunburst Hierarchy](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_sunburst.png)

#### Icicle Partition Chart (plotly-print: 59.2ms | Kaleido: 1517.1ms)

![Icicle Partition Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_icicle.png)

### Radial & Polar

#### Radar Performance Comparison (plotly-print: 124.3ms | Kaleido: 1667.7ms)

![Radar Performance Comparison](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatterpolar.png)

#### Polar Wind Rose (plotly-print: 81.7ms | Kaleido: 1785.0ms)

![Polar Wind Rose](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_barpolar.png)

### Specialized Diagrams

#### Energy Flow Sankey Diagram (plotly-print: 63.6ms | Kaleido: 1714.3ms)

![Energy Flow Sankey Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_sankey.png)

#### Parallel Categories Diagram (plotly-print: 66.5ms | Kaleido: 1661.2ms)

![Parallel Categories Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_parcats.png)

#### Formatted Data Table (plotly-print: 78.3ms | Kaleido: 1819.0ms)

![Formatted Data Table](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_table.png)

#### Carpet Coordinate Plot (plotly-print: 119.2ms | Kaleido: 1710.2ms)

![Carpet Coordinate Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_carpet.png)

### Layout edge cases

#### Bar chart with X labels at 45 deg (plotly-print: 110.8ms | Kaleido: 1804.5ms)

![Bar chart with X labels at 45 deg](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_rotated_ticks_45.png)

#### Bar chart with X labels at 90 deg (plotly-print: 127.6ms | Kaleido: 1886.6ms)

![Bar chart with X labels at 90 deg](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_rotated_ticks_90.png)

#### Annotation arrowheads (incl. circle) (plotly-print: 101.9ms | Kaleido: 1657.9ms)

![Annotation arrowheads (incl. circle)](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_annotations_arrowheads.png)

#### Long annotation arrows (dasharray length) (plotly-print: 98.6ms | Kaleido: 1803.9ms)

![Long annotation arrows (dasharray length)](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_annotations_long_arrows.png)

<!-- BENCHMARK-END -->

## Attribution

plotly-print is an independent project derived from [Mirage](https://github.com/ProfLear/mirage) by Benjamin Lear (MIT). Bundled plotly.js is copyright Plotly, Inc. (MIT); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
