from __future__ import annotations

import importlib.util

import plotly.graph_objects as go
import pytest
from benchmark.cases import CHARTS
from benchmark.compare import pixel_diff_mean
from benchmark.runner import QUICK_KEYS

import plotly_print

# Mean absolute channel difference vs Kaleido; quick suite currently peaks near ~3.2.
MEAN_DIFF_THRESHOLD = 10.0

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec('kaleido') is None,
    reason='kaleido is not installed (poe install)',
)


@pytest.fixture(scope='module', autouse=True)
def _warmup_engines() -> None:
    dummy = go.Figure(data=[go.Scatter(x=[1], y=[1])])
    plotly_print.to_image(dummy, format='png')
    dummy.to_image(format='png')


@pytest.mark.parametrize('key', QUICK_KEYS)
def test_quick_chart_mean_pixel_diff_vs_kaleido(key: str) -> None:
    fig = CHARTS[key]['fig']
    print_png = plotly_print.to_image(fig, format='png')
    kaleido_png = fig.to_image(format='png')

    mean_diff = pixel_diff_mean(print_png, kaleido_png)
    assert mean_diff is not None, f'{key}: image size mismatch vs Kaleido'
    assert mean_diff <= MEAN_DIFF_THRESHOLD, f'{key}: mean pixel diff {mean_diff:.2f} > {MEAN_DIFF_THRESHOLD}'
