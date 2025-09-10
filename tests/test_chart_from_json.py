from __future__ import annotations

import os
from pathlib import Path

from src_python_gui.atlas_graph_models import GraphRequest, Theme
from src_python_gui.chart_from_json import render_chart_from_json


def test_render_chart_from_json_tmp(tmp_path: Path) -> None:
    sample = "atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json"
    out = tmp_path / "spikes_py.png"
    req = GraphRequest(q="local-file", w=600, h=180, theme=Theme.LIGHT)
    render_chart_from_json(str(sample), str(out), req, overlay_wave=True, style="line")
    assert out.exists(), "PNG was not created"
    assert out.stat().st_size > 0, "PNG file is empty"
