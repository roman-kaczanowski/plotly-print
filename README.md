# plotly-print

[![CI](https://img.shields.io/github/actions/workflow/status/roman-kaczanowski/plotly-print/quality-checks.yml?branch=main&style=flat-square&label=CI)](https://github.com/roman-kaczanowski/plotly-print/actions/workflows/quality-checks.yml) [![PyPI](https://img.shields.io/pypi/v/plotly-print?style=flat-square)](https://pypi.org/project/plotly-print/) [![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://docs.python.org/3/) [![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

Lightweight, browser-less static image exporter for Plotly. No Chrome, Chromium, or Playwright. Figures are rendered with an embedded QuickJS runtime, Pillow font metrics, and `resvg-py` for raster output.

Works offline: a plotly.js 2D build is bundled (see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)).

## Install

```bash
pip install plotly-print
```

## Quickstart

```python
import plotly.express as px
import plotly_print

fig = px.scatter(x=[1, 2, 3, 4], y=[10, 11, 12, 13], title='Sales Growth')

svg = plotly_print.to_svg(fig)
png = plotly_print.to_image(fig, format='png', scale=2)
plotly_print.write_image(fig, 'chart.png')
```

Patch Plotly's `to_image` / `write_image` to use plotly-print:

```python
import plotly_print

plotly_print.register()
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and releases.

<!-- BENCHMARK-START -->

## Performance Benchmarks across 29 Chart Types

Empirical comparison of **plotly-print** vs **Kaleido** across 29 Plotly chart types (average per-image export latency after engine warmup):

| Category                 | Chart Type                                | plotly-print |  Kaleido  |  Speedup  |
| :----------------------- | :---------------------------------------- | :----------: | :-------: | :-------: |
| **Core Cartesian**       | Scatter & Line Chart                      | **88.9 ms**  | 1524.7 ms | **17.1x** |
| **Core Cartesian**       | Grouped Bar Chart                         | **93.5 ms**  | 1642.3 ms | **17.6x** |
| **Core Cartesian**       | Donut / Pie Chart                         | **74.4 ms**  | 1812.6 ms | **24.4x** |
| **Core Cartesian**       | Box Plot                                  | **93.5 ms**  | 1714.4 ms | **18.3x** |
| **Core Cartesian**       | Violin Plot                               | **86.5 ms**  | 1626.1 ms | **18.8x** |
| **Core Cartesian**       | Frequency Histogram                       | **105.5 ms** | 1556.6 ms | **14.8x** |
| **Core Cartesian**       | 2D Density Histogram                      | **105.5 ms** | 1696.5 ms | **16.1x** |
| **Core Cartesian**       | 2D Contour Plot                           | **135.8 ms** | 1744.5 ms | **12.8x** |
| **Core Cartesian**       | Performance Heatmap                       | **95.4 ms**  | 1647.1 ms | **17.3x** |
| **Core Cartesian**       | Ternary Phase Diagram                     | **95.8 ms**  | 1639.1 ms | **17.1x** |
| **Financial & Business** | Candlestick Stock Chart                   | **125.6 ms** | 1618.5 ms | **12.9x** |
| **Financial & Business** | OHLC Financial Chart                      | **159.2 ms** | 1686.0 ms | **10.6x** |
| **Financial & Business** | Waterfall Profit & Loss                   | **67.1 ms**  | 1561.6 ms | **23.3x** |
| **Financial & Business** | Sales Conversion Funnel                   | **102.3 ms** | 1620.2 ms | **15.8x** |
| **Financial & Business** | Funnel Area Analysis                      | **59.2 ms**  | 1593.7 ms | **26.9x** |
| **Financial & Business** | KPI Performance Indicator                 | **69.9 ms**  | 1607.4 ms | **23.0x** |
| **Hierarchical**         | Market Cap Treemap                        | **52.9 ms**  | 1672.0 ms | **31.6x** |
| **Hierarchical**         | Global Sunburst Hierarchy                 | **69.8 ms**  | 1665.6 ms | **23.9x** |
| **Hierarchical**         | Icicle Partition Chart                    | **59.8 ms**  | 1662.9 ms | **27.8x** |
| **Radial & Polar**       | Radar Performance Comparison              | **98.2 ms**  | 1689.3 ms | **17.2x** |
| **Radial & Polar**       | Polar Wind Rose                           | **78.3 ms**  | 1581.8 ms | **20.2x** |
| **Specialized Diagrams** | Energy Flow Sankey Diagram                | **47.6 ms**  | 1593.5 ms | **33.5x** |
| **Specialized Diagrams** | Parallel Categories Diagram               | **68.7 ms**  | 1551.1 ms | **22.6x** |
| **Specialized Diagrams** | Formatted Data Table                      | **96.7 ms**  | 1588.6 ms | **16.4x** |
| **Specialized Diagrams** | Carpet Coordinate Plot                    | **99.5 ms**  | 1647.8 ms | **16.6x** |
| **Layout edge cases**    | Bar chart with X labels at 45 deg         | **92.5 ms**  | 1741.8 ms | **18.8x** |
| **Layout edge cases**    | Bar chart with X labels at 90 deg         | **101.8 ms** | 1609.2 ms | **15.8x** |
| **Layout edge cases**    | Annotation arrowheads (incl. circle)      | **86.5 ms**  | 1663.2 ms | **19.2x** |
| **Layout edge cases**    | Long annotation arrows (dasharray length) | **93.3 ms**  | 1650.6 ms | **17.7x** |

> **Overall**: plotly-print is about **11x to 33x** faster across these charts, with no browser process.

## Visual Fidelity & Side-by-Side Comparisons

Side-by-side PNGs (Kaleido left, plotly-print right):

### Core Cartesian

#### Scatter & Line Chart (plotly-print: 88.9ms | Kaleido: 1524.7ms)

![Scatter & Line Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatter_line.png)

#### Grouped Bar Chart (plotly-print: 93.5ms | Kaleido: 1642.3ms)

![Grouped Bar Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_bar.png)

#### Donut / Pie Chart (plotly-print: 74.4ms | Kaleido: 1812.6ms)

![Donut / Pie Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_pie.png)

#### Box Plot (plotly-print: 93.5ms | Kaleido: 1714.4ms)

![Box Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_box.png)

#### Violin Plot (plotly-print: 86.5ms | Kaleido: 1626.1ms)

![Violin Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_violin.png)

#### Frequency Histogram (plotly-print: 105.5ms | Kaleido: 1556.6ms)

![Frequency Histogram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_histogram.png)

#### 2D Density Histogram (plotly-print: 105.5ms | Kaleido: 1696.5ms)

![2D Density Histogram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_histogram2d.png)

#### 2D Contour Plot (plotly-print: 135.8ms | Kaleido: 1744.5ms)

![2D Contour Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_contour.png)

#### Performance Heatmap (plotly-print: 95.4ms | Kaleido: 1647.1ms)

![Performance Heatmap](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_heatmap.png)

#### Ternary Phase Diagram (plotly-print: 95.8ms | Kaleido: 1639.1ms)

![Ternary Phase Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatterternary.png)

### Financial & Business

#### Candlestick Stock Chart (plotly-print: 125.6ms | Kaleido: 1618.5ms)

![Candlestick Stock Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_candlestick.png)

#### OHLC Financial Chart (plotly-print: 159.2ms | Kaleido: 1686.0ms)

![OHLC Financial Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_ohlc.png)

#### Waterfall Profit & Loss (plotly-print: 67.1ms | Kaleido: 1561.6ms)

![Waterfall Profit & Loss](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_waterfall.png)

#### Sales Conversion Funnel (plotly-print: 102.3ms | Kaleido: 1620.2ms)

![Sales Conversion Funnel](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_funnel.png)

#### Funnel Area Analysis (plotly-print: 59.2ms | Kaleido: 1593.7ms)

![Funnel Area Analysis](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_funnelarea.png)

#### KPI Performance Indicator (plotly-print: 69.9ms | Kaleido: 1607.4ms)

![KPI Performance Indicator](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_indicator.png)

### Hierarchical

#### Market Cap Treemap (plotly-print: 52.9ms | Kaleido: 1672.0ms)

![Market Cap Treemap](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_treemap.png)

#### Global Sunburst Hierarchy (plotly-print: 69.8ms | Kaleido: 1665.6ms)

![Global Sunburst Hierarchy](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_sunburst.png)

#### Icicle Partition Chart (plotly-print: 59.8ms | Kaleido: 1662.9ms)

![Icicle Partition Chart](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_icicle.png)

### Radial & Polar

#### Radar Performance Comparison (plotly-print: 98.2ms | Kaleido: 1689.3ms)

![Radar Performance Comparison](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_scatterpolar.png)

#### Polar Wind Rose (plotly-print: 78.3ms | Kaleido: 1581.8ms)

![Polar Wind Rose](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_barpolar.png)

### Specialized Diagrams

#### Energy Flow Sankey Diagram (plotly-print: 47.6ms | Kaleido: 1593.5ms)

![Energy Flow Sankey Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_sankey.png)

#### Parallel Categories Diagram (plotly-print: 68.7ms | Kaleido: 1551.1ms)

![Parallel Categories Diagram](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_parcats.png)

#### Formatted Data Table (plotly-print: 96.7ms | Kaleido: 1588.6ms)

![Formatted Data Table](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_table.png)

#### Carpet Coordinate Plot (plotly-print: 99.5ms | Kaleido: 1647.8ms)

![Carpet Coordinate Plot](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_carpet.png)

### Layout edge cases

#### Bar chart with X labels at 45 deg (plotly-print: 92.5ms | Kaleido: 1741.8ms)

![Bar chart with X labels at 45 deg](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_rotated_ticks_45.png)

#### Bar chart with X labels at 90 deg (plotly-print: 101.8ms | Kaleido: 1609.2ms)

![Bar chart with X labels at 90 deg](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_rotated_ticks_90.png)

#### Annotation arrowheads (incl. circle) (plotly-print: 86.5ms | Kaleido: 1663.2ms)

![Annotation arrowheads (incl. circle)](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_annotations_arrowheads.png)

#### Long annotation arrows (dasharray length) (plotly-print: 93.3ms | Kaleido: 1650.6ms)

![Long annotation arrows (dasharray length)](https://raw.githubusercontent.com/roman-kaczanowski/plotly-print/main/assets/benchmarks/compare_annotations_long_arrows.png)

<!-- BENCHMARK-END -->

## Attribution

plotly-print is an independent project derived from [Mirage](https://github.com/ProfLear/mirage) by Benjamin Lear (MIT). Bundled plotly.js is copyright Plotly, Inc. (MIT); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
