# plotly-print

[![CI](https://img.shields.io/github/actions/workflow/status/roman-kaczanowski/plotly-print/quality-checks.yml?branch=main&style=flat-square&label=CI)](https://github.com/roman-kaczanowski/plotly-print/actions/workflows/quality-checks.yml) [![PyPI](https://img.shields.io/pypi/v/plotly-print?style=flat-square)](https://pypi.org/project/plotly-print/) [![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://docs.python.org/3/) [![License](https://img.shields.io/badge/license-MIT-green?style=flat-square)](LICENSE)

Lightweight, browser-less static image exporter for Plotly. No Chrome, Chromium, or Playwright. Figures are rendered with an embedded QuickJS runtime, Pillow font metrics, and `resvg-py` for raster output.

Works offline: an official plotly.js cartesian partial is bundled (see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)).

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

## Attribution

plotly-print is an independent project derived from [Mirage](https://github.com/ProfLear/mirage) by Benjamin Lear (MIT). Bundled plotly.js is copyright Plotly, Inc. (MIT); see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
