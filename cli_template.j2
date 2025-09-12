import click
from pydantic_models import MultiCountryTotalInput
from helpers.manifest_parser import ManifestParser
from helpers.data_processor import DataProcessor
from helpers.query_builder import QueryBuilder
from helpers.api_client import AtlasApiClient

@click.group()
def atlas():
    """Atlas visualization commands."""
    pass

@atlas.group()
def visualize():
    """Visualization commands."""
    pass

@visualize.command("multi-country-total")
@click.option("--metric", required=True)
@click.option("--countries", multiple=True, required=True)
@click.option("--include-total", is_flag=True, default=False)
@click.option("--output", type=click.Path(), default="chart.png")
def multi_country_total(metric, countries, include_total, output):
    inputs = MultiCountryTotalInput(metric=metric, countries=list(countries), include_total=include_total)
    # Prefer dbt semantic manifest if present and recent
    metadata, *_ = ManifestParser().parse(prefer_semantic=True)
    df = DataProcessor(metadata, inputs).get_validated_data()
    query = QueryBuilder(df, inputs).build_asl()
    png = AtlasApiClient().get_graph(query)
    with open(output, "wb") as f:
        f.write(png)
    click.echo(f"Chart saved to {output}")

@visualize.command("metric-overview")
@click.option("--output", type=click.Path(), default="chart.png")
def metric_overview(output):
    """Minimal overview using dbt.duckdb data (total line)."""
    # Static inputs compatible with tests and QueryBuilder
    from pydantic_models import MultiCountryTotalInput
    inputs = MultiCountryTotalInput(metric="impressions", countries=["total"], include_total=False)
    # Use dbt.duckdb to build a quick overview DataFrame (country, impressions)
    metadata, *_ = ManifestParser().parse(prefer_semantic=True)
    df = DataProcessor(metadata, inputs).get_metric_overview_from_dbt()
    query = QueryBuilder(df, inputs).build_asl()
    png = AtlasApiClient().get_graph(query)
    with open(output, "wb") as f:
        f.write(png)
    click.echo(f"Chart saved to {output}")

@visualize.command("metric-timeseries")
@click.option("--metric", required=True)
@click.option("--days", type=int, default=14)
@click.option("--grain", type=click.Choice(["hour","day","week","month"]), default="day")
@click.option("--output", type=click.Path(), default="chart.png")
def metric_timeseries(metric, days, grain, output):
    """Render a time series for the last N days from dbt.duckdb."""
    from pydantic_models import MultiCountryTotalInput
    inputs = MultiCountryTotalInput(metric=metric, countries=["total"], include_total=False)
    metadata, *_ = ManifestParser().parse(prefer_semantic=True)
    df = DataProcessor(metadata, inputs).get_timeseries_from_dbt(metric=metric, days=days, grain=grain)
    query = QueryBuilder(df, inputs).build_time_asl()
    png = AtlasApiClient().get_graph(query)
    with open(output, "wb") as f:
        f.write(png)
    click.echo(f"Chart saved to {output}")

if __name__ == "__main__":
    atlas()
