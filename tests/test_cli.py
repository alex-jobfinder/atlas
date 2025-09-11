import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
import os
from click.testing import CliRunner
from pydantic_models import MultiCountryTotalInput
import atlas_cli
from helpers.api_client import AtlasApiClient


def test_cli_multi_country_total(tmp_path, monkeypatch):
    output = tmp_path / "chart.png"
    def fake_graph(self, query):
        return b"pngdata"
    monkeypatch.setattr(AtlasApiClient, "get_graph", fake_graph)
    runner = CliRunner()
    result = runner.invoke(atlas_cli.atlas, [
        "visualize", "multi-country-total",
        "--metric", "impressions",
        "--countries", "US",
        "--countries", "CA",
        "--include-total",
        "--output", str(output)
    ])
    assert result.exit_code == 0
    assert output.exists()
    assert output.read_bytes() == b"pngdata"
