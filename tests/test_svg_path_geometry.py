"""Regression tests for SVG path/line geometry in micro_dom.js."""

from __future__ import annotations

import json
import math
import os
import re

import plotly.graph_objects as go
import pytest
import quickjs

import plotly_print

_MICRO_DOM = os.path.join(os.path.dirname(__file__), '..', 'src', 'plotly_print', 'js', 'micro_dom.js')


def _micro_dom_context() -> quickjs.Context:
    ctx = quickjs.Context()
    ctx.set_max_stack_size(10 * 1024 * 1024)
    with open(_MICRO_DOM, encoding='utf-8') as f:
        ctx.eval(f.read())
    return ctx


def _eval_json(js: str) -> dict:
    ctx = _micro_dom_context()
    return json.loads(ctx.eval(js))


def test_path_line_total_length_and_point_at_tip():
    """Arrow paths are M x0,y0 L x1,y1 — tip must not collapse to (0,0)."""
    data = _eval_json(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            var p = document.createElementNS(NS, 'path');
            p.setAttribute('d', 'M100,200L250,350');
            var tip = p.getPointAtLength(p.getTotalLength());
            var mid = p.getPointAtLength(p.getTotalLength() / 2);
            var bb = p.getBBox();
            return JSON.stringify({
                total: p.getTotalLength(),
                tip: tip,
                mid: mid,
                bb: {x: bb.x, y: bb.y, w: bb.width, h: bb.height},
                at0: p.getPointAtLength(0),
                clampNeg: p.getPointAtLength(-10),
                clampOver: p.getPointAtLength(1e9)
            });
        })()
        """
    )
    expected = math.hypot(150, 150)
    assert data['total'] == pytest.approx(expected)
    assert data['tip']['x'] == pytest.approx(250)
    assert data['tip']['y'] == pytest.approx(350)
    assert data['mid']['x'] == pytest.approx(175)
    assert data['mid']['y'] == pytest.approx(275)
    assert data['at0']['x'] == pytest.approx(100)
    assert data['at0']['y'] == pytest.approx(200)
    assert data['clampNeg']['x'] == pytest.approx(100)
    assert data['clampOver']['x'] == pytest.approx(250)
    assert data['bb']['x'] == pytest.approx(100)
    assert data['bb']['y'] == pytest.approx(200)
    assert data['bb']['w'] == pytest.approx(150)
    assert data['bb']['h'] == pytest.approx(150)


def test_path_relative_and_implicit_commands():
    data = _eval_json(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            var p = document.createElementNS(NS, 'path');
            // M then implicit L; relative l; H/V; Z — closed 30x30 rect
            p.setAttribute('d', 'M10,10 40,10 l0,30 H10 V10 Z');
            var bb = p.getBBox();
            return JSON.stringify({
                total: p.getTotalLength(),
                bb: {x: bb.x, y: bb.y, w: bb.width, h: bb.height},
                tip: p.getPointAtLength(p.getTotalLength())
            });
        })()
        """
    )
    # Closed 30x30 rectangle perimeter
    assert data['total'] == pytest.approx(120)
    assert data['bb']['x'] == pytest.approx(10)
    assert data['bb']['y'] == pytest.approx(10)
    assert data['bb']['w'] == pytest.approx(30)
    assert data['bb']['h'] == pytest.approx(30)
    assert data['tip']['x'] == pytest.approx(10)
    assert data['tip']['y'] == pytest.approx(10)


def test_path_numbers_with_signs_and_exponents():
    data = _eval_json(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            var p = document.createElementNS(NS, 'path');
            p.setAttribute('d', 'M0,0L1e2-50');
            var tip = p.getPointAtLength(p.getTotalLength());
            return JSON.stringify({total: p.getTotalLength(), tip: tip});
        })()
        """
    )
    assert data['total'] == pytest.approx(math.hypot(100, -50))
    assert data['tip']['x'] == pytest.approx(100)
    assert data['tip']['y'] == pytest.approx(-50)


def test_line_element_geometry():
    data = _eval_json(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            var el = document.createElementNS(NS, 'line');
            el.setAttribute('x1', '10');
            el.setAttribute('y1', '20');
            el.setAttribute('x2', '40');
            el.setAttribute('y2', '60');
            var bb = el.getBBox();
            var tip = el.getPointAtLength(el.getTotalLength());
            return JSON.stringify({
                total: el.getTotalLength(),
                tip: tip,
                bb: {x: bb.x, y: bb.y, w: bb.width, h: bb.height}
            });
        })()
        """
    )
    assert data['total'] == pytest.approx(50)
    assert data['tip']['x'] == pytest.approx(40)
    assert data['tip']['y'] == pytest.approx(60)
    assert data['bb']['x'] == pytest.approx(10)
    assert data['bb']['y'] == pytest.approx(20)
    assert data['bb']['w'] == pytest.approx(30)
    assert data['bb']['h'] == pytest.approx(40)


def test_rect_circle_ellipse_bbox():
    data = _eval_json(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            var rect = document.createElementNS(NS, 'rect');
            rect.setAttribute('x', '5');
            rect.setAttribute('y', '7');
            rect.setAttribute('width', '20');
            rect.setAttribute('height', '10');
            var circle = document.createElementNS(NS, 'circle');
            circle.setAttribute('cx', '50');
            circle.setAttribute('cy', '60');
            circle.setAttribute('r', '8');
            var ellipse = document.createElementNS(NS, 'ellipse');
            ellipse.setAttribute('cx', '100');
            ellipse.setAttribute('cy', '200');
            ellipse.setAttribute('rx', '15');
            ellipse.setAttribute('ry', '5');
            // Own transform must not affect getBBox.
            circle.setAttribute('transform', 'translate(1000,1000)');
            var rb = rect.getBBox();
            var cb = circle.getBBox();
            var eb = ellipse.getBBox();
            return JSON.stringify({
                rect: {x: rb.x, y: rb.y, w: rb.width, h: rb.height},
                circle: {x: cb.x, y: cb.y, w: cb.width, h: cb.height},
                ellipse: {x: eb.x, y: eb.y, w: eb.width, h: eb.height}
            });
        })()
        """
    )
    assert data['rect'] == {'x': 5, 'y': 7, 'w': 20, 'h': 10}
    assert data['circle']['x'] == pytest.approx(42)
    assert data['circle']['y'] == pytest.approx(52)
    assert data['circle']['w'] == pytest.approx(16)
    assert data['circle']['h'] == pytest.approx(16)
    assert data['ellipse']['x'] == pytest.approx(85)
    assert data['ellipse']['y'] == pytest.approx(195)
    assert data['ellipse']['w'] == pytest.approx(30)
    assert data['ellipse']['h'] == pytest.approx(10)


def test_cubic_and_arc_sampling_reach_endpoint():
    data = _eval_json(
        r"""
        (function() {
            var NS = 'http://www.w3.org/2000/svg';
            var cubic = document.createElementNS(NS, 'path');
            cubic.setAttribute('d', 'M0,0C10,0 20,0 30,0');
            var arc = document.createElementNS(NS, 'path');
            arc.setAttribute('d', 'M100,0A50,50 0 0 1 50,50');
            var ct = cubic.getPointAtLength(cubic.getTotalLength());
            var at = arc.getPointAtLength(arc.getTotalLength());
            return JSON.stringify({
                cubicTotal: cubic.getTotalLength(),
                cubicTip: ct,
                arcTip: at,
                arcTotal: arc.getTotalLength()
            });
        })()
        """
    )
    assert data['cubicTip']['x'] == pytest.approx(30, abs=0.01)
    assert data['cubicTip']['y'] == pytest.approx(0, abs=0.01)
    assert data['cubicTotal'] == pytest.approx(30, abs=0.5)
    assert data['arcTip']['x'] == pytest.approx(50, abs=0.5)
    assert data['arcTip']['y'] == pytest.approx(50, abs=0.5)
    assert data['arcTotal'] > 70  # quarter circle of r=50 ≈ 78.5


def test_annotation_arrowhead_not_at_origin():
    """plotly.js places heads with translate(tip); tip comes from getPointAtLength."""
    fig = go.Figure(
        data=[go.Scatter(x=[1, 2, 3, 4], y=[10, 15, 13, 17], mode='lines')],
        layout=go.Layout(
            width=500,
            height=400,
            title='Arrowheads',
            annotations=[
                dict(x=3, y=13, ax=40, ay=-60, text='C', showarrow=True, arrowhead=6, arrowsize=1.5),
                dict(x=2, y=15, ax=-50, ay=-40, text='T', showarrow=True, arrowhead=2),
            ],
        ),
    )
    svg = plotly_print.to_svg(fig)

    arrow_groups = re.findall(
        r'<g class="annotation-arrow-g"[^>]*>(.*?)</g>',
        svg,
        flags=re.DOTALL,
    )
    assert len(arrow_groups) == 2

    for group in arrow_groups:
        paths = re.findall(r'<path\b[^>]*/?>', group)
        assert len(paths) >= 2, 'expected shaft path + arrowhead path'

        shaft, head = paths[0], paths[1]
        d_attr = re.search(r'\bd="([^"]+)"', shaft)
        assert d_attr, shaft
        coords = [float(x) for x in re.findall(r'[+-]?(?:\d*\.\d+|\d+)(?:[eE][+-]?\d+)?', d_attr.group(1))]
        assert len(coords) >= 4, d_attr.group(1)
        x0, y0, tip_x, tip_y = coords[0], coords[1], coords[-2], coords[-1]
        shaft_len = math.hypot(tip_x - x0, tip_y - y0)

        transform = re.search(r'\btransform="([^"]*)"', head)
        assert transform and transform.group(1), f'missing head transform: {head}'
        tr = re.search(r'translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)', transform.group(1))
        assert tr, f'expected translate(tip) on head: {head}'
        hx, hy = float(tr.group(1)), float(tr.group(2))
        # Bug: getPointAtLength returned (0,0) so strTranslate emitted '' / origin.
        assert abs(hx) > 1 or abs(hy) > 1
        # Triangle heads sit slightly before the geometric tip; circle heads on it.
        assert math.hypot(hx - tip_x, hy - tip_y) < 5

        dash = re.search(r'stroke-dasharray:\s*([^;"]+)', shaft)
        assert dash, f'missing stroke-dasharray on shaft: {shaft}'
        nums = [float(x) for x in re.findall(r'[-\d.]+', dash.group(1))]
        assert max(nums) == pytest.approx(shaft_len, abs=2.0)
