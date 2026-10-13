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

On this run, plotly-print exported all 30 chart types **12x to 33x faster** than Kaleido.

These are mean per-image PNG export times after both engines were warmed up. Timings are machine-specific; use the side-by-side images below to evaluate rendering differences.

See the [raw results](assets/benchmarks/benchmark_summary.json) or [run the benchmark locally](CONTRIBUTING.md#kaleido-visual-benchmark).

| Category                 | Chart Type                                |  Kaleido  | plotly-print |  Speedup  |
| :----------------------- | :---------------------------------------- | :-------: | :----------: | :-------: |
| **Core Cartesian**       | Scatter & Line Chart                      | 1668.5 ms | **88.2 ms**  | **18.9x** |
| **Core Cartesian**       | Grouped Bar Chart                         | 1758.1 ms | **81.3 ms**  | **21.6x** |
| **Core Cartesian**       | Donut / Pie Chart                         | 1628.6 ms | **73.6 ms**  | **22.1x** |
| **Core Cartesian**       | Box Plot                                  | 1748.2 ms | **77.1 ms**  | **22.7x** |
| **Core Cartesian**       | Violin Plot                               | 1623.8 ms | **84.1 ms**  | **19.3x** |
| **Core Cartesian**       | Frequency Histogram                       | 1878.0 ms | **62.7 ms**  | **30.0x** |
| **Core Cartesian**       | 2D Density Histogram                      | 1949.4 ms | **98.8 ms**  | **19.7x** |
| **Core Cartesian**       | 2D Contour Plot                           | 1604.9 ms | **118.7 ms** | **13.5x** |
| **Core Cartesian**       | Performance Heatmap                       | 1832.4 ms | **87.3 ms**  | **21.0x** |
| **Core Cartesian**       | Ternary Phase Diagram                     | 1724.9 ms | **84.9 ms**  | **20.3x** |
| **Financial & Business** | Candlestick Stock Chart                   | 1741.1 ms | **140.5 ms** | **12.4x** |
| **Financial & Business** | OHLC Financial Chart                      | 1670.0 ms | **131.3 ms** | **12.7x** |
| **Financial & Business** | Waterfall Profit & Loss                   | 1793.0 ms | **64.7 ms**  | **27.7x** |
| **Financial & Business** | Sales Conversion Funnel                   | 1629.9 ms | **91.1 ms**  | **17.9x** |
| **Financial & Business** | Funnel Area Analysis                      | 1694.0 ms | **61.7 ms**  | **27.5x** |
| **Financial & Business** | KPI Performance Indicator                 | 1634.1 ms | **57.2 ms**  | **28.6x** |
| **Hierarchical**         | Market Cap Treemap                        | 1625.4 ms | **52.6 ms**  | **30.9x** |
| **Hierarchical**         | Global Sunburst Hierarchy                 | 1723.9 ms | **61.8 ms**  | **27.9x** |
| **Hierarchical**         | Icicle Partition Chart                    | 1594.7 ms | **50.2 ms**  | **31.7x** |
| **Radial & Polar**       | Radar Performance Comparison              | 2481.9 ms | **96.5 ms**  | **25.7x** |
| **Radial & Polar**       | Polar Wind Rose                           | 1826.6 ms | **77.5 ms**  | **23.6x** |
| **Specialized Diagrams** | Energy Flow Sankey Diagram                | 1708.4 ms | **51.7 ms**  | **33.1x** |
| **Specialized Diagrams** | Parallel Categories Diagram               | 1620.2 ms | **57.0 ms**  | **28.4x** |
| **Specialized Diagrams** | Formatted Data Table                      | 1766.4 ms | **69.9 ms**  | **25.3x** |
| **Specialized Diagrams** | Carpet Coordinate Plot                    | 1792.2 ms | **86.1 ms**  | **20.8x** |
| **Layout edge cases**    | Bar chart with X labels at 45 deg         | 1673.2 ms | **89.0 ms**  | **18.8x** |
| **Layout edge cases**    | Bar chart with X labels at 90 deg         | 1883.9 ms | **87.7 ms**  | **21.5x** |
| **Layout edge cases**    | Annotation arrowheads (incl. circle)      | 1661.6 ms | **82.4 ms**  | **20.2x** |
| **Layout edge cases**    | Long annotation arrows (dasharray length) | 1719.1 ms | **79.7 ms**  | **21.6x** |
| **Layout edge cases**    | Table cells with HTML markup and entities | 1692.5 ms | **74.8 ms**  | **22.6x** |

## Visual comparisons

Side-by-side PNGs (Kaleido left, plotly-print right):

### Core Cartesian

#### Scatter & Line Chart (plotly-print: 88.2ms | Kaleido: 1668.5ms)

![Scatter & Line Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatter_line.png)

#### Grouped Bar Chart (plotly-print: 81.3ms | Kaleido: 1758.1ms)

![Grouped Bar Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_bar.png)

#### Donut / Pie Chart (plotly-print: 73.6ms | Kaleido: 1628.6ms)

![Donut / Pie Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_pie.png)

#### Box Plot (plotly-print: 77.1ms | Kaleido: 1748.2ms)

![Box Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_box.png)

#### Violin Plot (plotly-print: 84.1ms | Kaleido: 1623.8ms)

![Violin Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_violin.png)

#### Frequency Histogram (plotly-print: 62.7ms | Kaleido: 1878.0ms)

![Frequency Histogram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_histogram.png)

#### 2D Density Histogram (plotly-print: 98.8ms | Kaleido: 1949.4ms)

![2D Density Histogram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_histogram2d.png)

#### 2D Contour Plot (plotly-print: 118.7ms | Kaleido: 1604.9ms)

![2D Contour Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_contour.png)

#### Performance Heatmap (plotly-print: 87.3ms | Kaleido: 1832.4ms)

![Performance Heatmap](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_heatmap.png)

#### Ternary Phase Diagram (plotly-print: 84.9ms | Kaleido: 1724.9ms)

![Ternary Phase Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatterternary.png)

### Financial & Business

#### Candlestick Stock Chart (plotly-print: 140.5ms | Kaleido: 1741.1ms)

![Candlestick Stock Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_candlestick.png)

#### OHLC Financial Chart (plotly-print: 131.3ms | Kaleido: 1670.0ms)

![OHLC Financial Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_ohlc.png)

#### Waterfall Profit & Loss (plotly-print: 64.7ms | Kaleido: 1793.0ms)

![Waterfall Profit & Loss](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_waterfall.png)

#### Sales Conversion Funnel (plotly-print: 91.1ms | Kaleido: 1629.9ms)

![Sales Conversion Funnel](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_funnel.png)

#### Funnel Area Analysis (plotly-print: 61.7ms | Kaleido: 1694.0ms)

![Funnel Area Analysis](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_funnelarea.png)

#### KPI Performance Indicator (plotly-print: 57.2ms | Kaleido: 1634.1ms)

![KPI Performance Indicator](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_indicator.png)

### Hierarchical

#### Market Cap Treemap (plotly-print: 52.6ms | Kaleido: 1625.4ms)

![Market Cap Treemap](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_treemap.png)

#### Global Sunburst Hierarchy (plotly-print: 61.8ms | Kaleido: 1723.9ms)

![Global Sunburst Hierarchy](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_sunburst.png)

#### Icicle Partition Chart (plotly-print: 50.2ms | Kaleido: 1594.7ms)

![Icicle Partition Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_icicle.png)

### Radial & Polar

#### Radar Performance Comparison (plotly-print: 96.5ms | Kaleido: 2481.9ms)

![Radar Performance Comparison](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatterpolar.png)

#### Polar Wind Rose (plotly-print: 77.5ms | Kaleido: 1826.6ms)

![Polar Wind Rose](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_barpolar.png)

### Specialized Diagrams

#### Energy Flow Sankey Diagram (plotly-print: 51.7ms | Kaleido: 1708.4ms)

![Energy Flow Sankey Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_sankey.png)

#### Parallel Categories Diagram (plotly-print: 57.0ms | Kaleido: 1620.2ms)

![Parallel Categories Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_parcats.png)

#### Formatted Data Table (plotly-print: 69.9ms | Kaleido: 1766.4ms)

![Formatted Data Table](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_table.png)

#### Carpet Coordinate Plot (plotly-print: 86.1ms | Kaleido: 1792.2ms)

![Carpet Coordinate Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_carpet.png)

### Layout edge cases

#### Bar chart with X labels at 45 deg (plotly-print: 89.0ms | Kaleido: 1673.2ms)

![Bar chart with X labels at 45 deg](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_rotated_ticks_45.png)

#### Bar chart with X labels at 90 deg (plotly-print: 87.7ms | Kaleido: 1883.9ms)

![Bar chart with X labels at 90 deg](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_rotated_ticks_90.png)

#### Annotation arrowheads (incl. circle) (plotly-print: 82.4ms | Kaleido: 1661.6ms)

![Annotation arrowheads (incl. circle)](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_annotations_arrowheads.png)

#### Long annotation arrows (dasharray length) (plotly-print: 79.7ms | Kaleido: 1719.1ms)

![Long annotation arrows (dasharray length)](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_annotations_long_arrows.png)

#### Table cells with HTML markup and entities (plotly-print: 74.8ms | Kaleido: 1692.5ms)

![Table cells with HTML markup and entities](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_table_markup.png)

<!-- BENCHMARK-END -->

## Attribution

plotly-print is an independent project derived from [Mirage](https://github.com/ProfLear/mirage) by Benjamin Lear (MIT). Bundled plotly.js is copyright Plotly, Inc. (MIT); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
