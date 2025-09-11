import sys, pathlib; sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))
import pandas as pd
import pytest

from pydantic_models import MultiCountryTotalInput
from helpers.manifest_parser import ManifestParser
from helpers.data_processor import DataProcessor
from helpers.query_builder import QueryBuilder
from helpers.api_client import AtlasApiClient

# ManifestParser tests

def test_parse_valid_manifest():
    metadata, MetricEnum, DimensionEnum, AggregationEnum = ManifestParser("manifest.json").parse()
    assert "minute_ad_events.impressions" in metadata["metrics"]
    assert MetricEnum.IMPRESSIONS.value == "minute_ad_events.impressions"
    assert DimensionEnum.COUNTRY.value == "country"
    assert AggregationEnum.SUM.value == "sum"

def test_parse_missing_manifest(tmp_path):
    missing = tmp_path / "manifest.json"
    parser = ManifestParser(missing)
    with pytest.raises(FileNotFoundError):
        parser.parse()

# DataProcessor tests

def _metadata():
    metadata, *_ = ManifestParser("manifest.json").parse()
    return metadata

def test_get_validated_data_single_metric():
    inputs = MultiCountryTotalInput(metric="impressions", countries=["US"], include_total=False)
    df = DataProcessor(_metadata(), inputs).get_validated_data()
    assert set(df["country"]) == {"US"}
    assert df.iloc[0]["impressions"] == 45

def test_get_validated_data_multi_country():
    inputs = MultiCountryTotalInput(metric="impressions", countries=["US", "CA"], include_total=True)
    df = DataProcessor(_metadata(), inputs).get_validated_data()
    assert set(df["country"]) == {"US", "CA", "total"}
    total = df[df["country"] == "total"]["impressions"].iloc[0]
    assert total == df[df["country"] != "total"]["impressions"].sum()

def test_get_validated_data_invalid_dimension():
    inputs = MultiCountryTotalInput(metric="impressions", countries=["US"], include_total=False, dimension="region")
    with pytest.raises(ValueError):
        DataProcessor(_metadata(), inputs).get_validated_data()

# QueryBuilder tests

def test_build_asl_single_metric():
    inputs = MultiCountryTotalInput(metric="impressions", countries=["US"], include_total=False)
    df = pd.DataFrame({"country": ["US"], "impressions": [100]})
    query = QueryBuilder(df, inputs).build_asl()
    assert query["expressions"] == [{"label": "US", "value": 100}]

def test_build_asl_multi_country_total():
    inputs = MultiCountryTotalInput(metric="impressions", countries=["US", "CA"], include_total=True)
    df = pd.DataFrame({"country": ["US", "CA", "total"], "impressions": [1,2,3]})
    query = QueryBuilder(df, inputs).build_asl()
    labels = [e["label"] for e in query["expressions"]]
    assert labels == ["US", "CA", "total"]

def test_build_asl_no_expressions():
    inputs = MultiCountryTotalInput(metric="impressions", countries=[], include_total=False)
    df = pd.DataFrame({"country": [], "impressions": []})
    with pytest.raises(ValueError):
        QueryBuilder(df, inputs).build_asl()

# AtlasApiClient tests

def test_get_graph_success(monkeypatch):
    def fake_post(url, json):
        class Resp:
            status_code = 200
            headers = {"Content-Type": "image/png"}
            content = b"data"
            def raise_for_status(self):
                return None
        return Resp()
    monkeypatch.setattr("requests.post", fake_post)
    png = AtlasApiClient().get_graph({"test": 1})
    assert png == b"data"

def test_get_graph_http_error(monkeypatch):
    def fake_post(url, json):
        class Resp:
            status_code = 404
            headers = {"Content-Type": "image/png"}
            content = b""
            def raise_for_status(self):
                from requests import HTTPError
                raise HTTPError("404")
        return Resp()
    monkeypatch.setattr("requests.post", fake_post)
    with pytest.raises(Exception):
        AtlasApiClient().get_graph({})

def test_get_graph_non_png_response(monkeypatch):
    def fake_post(url, json):
        class Resp:
            status_code = 200
            headers = {"Content-Type": "text/plain"}
            content = b"data"
            def raise_for_status(self):
                return None
        return Resp()
    monkeypatch.setattr("requests.post", fake_post)
    with pytest.raises(ValueError):
        AtlasApiClient().get_graph({})
