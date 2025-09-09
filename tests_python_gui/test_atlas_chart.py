from __future__ import annotations

from src_python_gui.atlas_chart import GraphQuery, build_graph_url, fetch_chart


def test_build_graph_url_basic():
    q = GraphQuery(expr="name,foo,:eq,:sum", start="e-1h")
    url = build_graph_url("http://localhost:7101", q)
    assert url.startswith("http://localhost:7101/api/v1/graph?")
    assert "q=name%2Cfoo%2C%3Aeq%2C%3Asum" in url
    assert "s=e-1h" in url


def test_fetch_chart_writes_file(tmp_path, monkeypatch):
    class DummyResp:
        status_code = 200
        content = b"PNGDATA"

        def raise_for_status(self):
            return None

    def fake_get(url, timeout=10.0):
        return DummyResp()

    import requests

    monkeypatch.setattr(requests, "get", fake_get)

    out = tmp_path / "chart.png"
    fetch_chart("http://example/api/v1/graph?q=x", str(out))
    assert out.exists()
    assert out.read_bytes() == b"PNGDATA"
