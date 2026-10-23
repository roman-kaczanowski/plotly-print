"""Tests for figure values that are not natively JSON-serializable."""

import datetime as dt
import decimal
import json

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

import plotly_print
from plotly_print.engine import _expand_typed_arrays


@pytest.mark.parametrize(
    'name,fig',
    [
        (
            'datetime',
            go.Figure(
                data=[
                    go.Scatter(
                        x=[dt.datetime(2024, 1, 1), dt.datetime(2024, 1, 2), dt.datetime(2024, 1, 3)], y=[1, 2, 3]
                    )
                ],
                layout=go.Layout(
                    title='Datetime',
                    width=500,
                    height=350,
                    xaxis={'range': [dt.datetime(2024, 1, 1), dt.datetime(2024, 1, 4)]},
                ),
            ),
        ),
        (
            'date',
            go.Figure(
                data=[go.Scatter(x=[dt.date(2024, 1, 1), dt.date(2024, 1, 2), dt.date(2024, 1, 3)], y=[1, 2, 3])],
                layout=go.Layout(title='Date', width=500, height=350),
            ),
        ),
        (
            'time',
            go.Figure(
                data=[go.Scatter(x=[dt.time(1, 0), dt.time(2, 0), dt.time(3, 0)], y=[1, 2, 3])],
                layout=go.Layout(title='Time', width=500, height=350),
            ),
        ),
        (
            'decimal',
            go.Figure(
                data=[
                    go.Scatter(
                        x=[decimal.Decimal('1.5'), decimal.Decimal('2.5'), decimal.Decimal('3.5')],
                        y=[decimal.Decimal('10'), decimal.Decimal('20'), decimal.Decimal('30')],
                    )
                ],
                layout=go.Layout(
                    title='Decimal',
                    width=500,
                    height=350,
                    annotations=[
                        {'x': decimal.Decimal('2.5'), 'y': decimal.Decimal('20'), 'text': 'note', 'showarrow': False}
                    ],
                    xaxis={
                        'tickvals': [decimal.Decimal('1.5'), decimal.Decimal('2.5'), decimal.Decimal('3.5')],
                        'ticktext': ['a', 'b', 'c'],
                    },
                ),
            ),
        ),
        (
            'numpy-datetime64',
            go.Figure(
                data=[
                    go.Scatter(
                        x=np.array(['2024-01-01', '2024-01-02', '2024-01-03'], dtype='datetime64[D]'),
                        y=np.array([1, 2, 3]),
                    )
                ],
                layout=go.Layout(title='Numpy datetime64', width=500, height=350),
            ),
        ),
        (
            'numpy-object-array',
            go.Figure(
                data=[
                    go.Bar(
                        x=np.array(['alpha', 'beta', 'gamma'], dtype=object),
                        y=np.array(
                            [decimal.Decimal('1.5'), decimal.Decimal('2.5'), decimal.Decimal('4')], dtype=object
                        ),
                    )
                ],
                layout=go.Layout(title='Numpy object array', width=500, height=350),
            ),
        ),
        (
            'pandas-timestamp',
            go.Figure(
                data=[go.Scatter(x=[pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-02'), pd.NaT], y=[1, 2, 3])],
                layout=go.Layout(
                    title='Timestamp',
                    width=500,
                    height=350,
                    xaxis={'range': [pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-05')]},
                ),
            ),
        ),
        (
            'pandas-timestamp-series',
            go.Figure(
                data=[go.Scatter(x=pd.Series(pd.date_range('2024-01-01', periods=3)), y=pd.Series([1, 2, 3]))],
                layout=go.Layout(title='Timestamp series', width=500, height=350),
            ),
        ),
        (
            'pandas-timedelta',
            go.Figure(
                data=[go.Scatter(x=[pd.Timedelta(days=1), pd.Timedelta(days=2), pd.Timedelta(days=3)], y=[1, 2, 3])],
                layout=go.Layout(title='Timedelta', width=500, height=350),
            ),
        ),
        (
            'pandas-na',
            go.Figure(
                data=[go.Scatter(x=[1, 2, 3, 4], y=[1, pd.NA, 3, pd.NA])],
                layout=go.Layout(title='Pandas NA', width=500, height=350),
            ),
        ),
    ],
)
def test_non_json_values_render(name, fig):
    svg = plotly_print.to_svg(fig)
    assert '<svg' in svg
    png = plotly_print.to_image(fig, format='png')
    assert png.startswith(b'\x89PNG')


def test_typed_array_specs_expand_to_plain_values():
    x = np.array([1.5, -2.25], dtype=np.float64)
    y = np.array([-1, 2, 3, 4], dtype=np.int8)
    color = np.array([0.25, 0.5], dtype=np.float32)
    size = np.array([10, 20], dtype=np.uint16)
    z = np.arange(4, dtype=np.float64).reshape(2, 2)
    fig = go.Figure(
        data=[
            go.Scatter(x=x, y=y, marker={'color': color, 'size': size}),
            go.Heatmap(z=z),
        ]
    )

    expanded = _expand_typed_arrays(fig.to_dict())

    assert expanded['data'][0]['x'] == x.tolist()
    assert expanded['data'][0]['y'] == y.tolist()
    assert expanded['data'][0]['marker']['color'] == color.tolist()
    assert expanded['data'][0]['marker']['size'] == size.tolist()
    assert expanded['data'][1]['z'] == z.tolist()


@pytest.mark.parametrize('source', ['figure', 'to_dict', 'json'])
def test_padded_numpy_bdata_renders(source):
    # 22 float64 values are 176 bytes, which is not a multiple of 3, so the
    # base64 payload has padding that used to crash QuickJS.
    values = np.arange(22, dtype=float)
    fig = go.Figure(
        data=[go.Scatter(x=values, y=values, mode='lines+markers')],
        layout=go.Layout(width=400, height=300, title='Bdata'),
    )
    if source == 'to_dict':
        fig = fig.to_dict()
    elif source == 'json':
        fig = json.loads(fig.to_json())

    svg = plotly_print.to_svg(fig)
    assert '<svg' in svg
    assert 'Bdata' in svg
    assert 'class="point"' in svg


def test_padded_pandas_and_heatmap_render():
    series = pd.Series(np.arange(22, dtype=float))
    figures = [
        go.Figure(data=[go.Scatter(x=series, y=series**2)], layout=go.Layout(width=400, height=300)),
        go.Figure(
            data=[go.Heatmap(z=np.arange(4, dtype=float).reshape(2, 2))], layout=go.Layout(width=400, height=300)
        ),
        go.Figure(data=[go.Bar(y=np.array([1, 2], dtype=np.int16))], layout=go.Layout(width=400, height=300)),
    ]
    for fig in figures:
        svg = plotly_print.to_svg(fig)
        assert '<svg' in svg


def test_hooked_to_image_with_decimal_values():
    plotly_print.register()

    fig = go.Figure(
        data=[
            go.Scatter(
                x=[decimal.Decimal('1'), decimal.Decimal('2'), decimal.Decimal('3')],
                y=[decimal.Decimal('4'), decimal.Decimal('5'), decimal.Decimal('6')],
            )
        ],
        layout=go.Layout(title='Hooked decimal', width=400, height=300),
    )

    # Calling fig.to_image() directly
    img_bytes = fig.to_image(format='png')
    assert img_bytes.startswith(b'\x89PNG')

    plotly_print.unregister()
