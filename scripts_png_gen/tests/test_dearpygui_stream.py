import json
import gzip
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from scripts_png_gen.dearpygui_stream import _load_graph


def _sample_data():
    return [
        {"type": "timeseries", "label": "cpu", "data": {"values": [1, 2, 3]}},
        {"type": "graph-metadata", "startTime": 0, "step": 1000},
    ]


def test_load_graph(tmp_path):
    path = tmp_path / "sample.v2.json"
    path.write_text(json.dumps(_sample_data()))
    ts, series = _load_graph(path)
    assert ts == [0, 1, 2]
    assert series[0]["label"] == "cpu"


def test_load_graph_gz(tmp_path):
    path = tmp_path / "sample.v2.json.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        json.dump(_sample_data(), f)
    ts, _ = _load_graph(path)
    assert ts[-1] == 2


def test_cli_help():
    script = Path(__file__).resolve().parents[1] / "dearpygui_stream.py"
    result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True)
    assert result.returncode == 0
    assert "Visualize Atlas graph output" in result.stdout
