from __future__ import annotations

from pathlib import Path

from src_python_gui.atlas_graph_models import GraphRequest, Theme
from src_python_gui.chart_from_json import render_chart_from_json


def test_render_chart_from_local_json(tmp_path: Path):
    # Use the bundled test JSON from atlas-chart resources
    json_path = "atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json"
    out = tmp_path / "spikes_light.png"

    req = GraphRequest(q="local", theme=Theme.LIGHT, w=700, h=200)
    render_chart_from_json(
        json_path,
        str(out),
        request=req,
        overlay_wave=True,
        style="area",
        axis_groups=[0, 1],
        ylabel_left="GC",
        ylabel_right="Wave",
    )

    assert out.exists()
    data = out.read_bytes()
    # PNG signature
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
