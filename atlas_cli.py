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
    metadata, *_ = ManifestParser().parse()
    df = DataProcessor(metadata, inputs).get_validated_data()
    query = QueryBuilder(df, inputs).build_asl()
    png = AtlasApiClient().get_graph(query)
    with open(output, "wb") as f:
        f.write(png)
    click.echo(f"Chart saved to {output}")

if __name__ == "__main__":
    atlas()
