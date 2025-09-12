from __future__ import annotations
import duckdb
import pandas as pd
from pathlib import Path
from typing import Dict

class DataProcessor:
    """Runs DuckDB queries against local Parquet data."""

    def __init__(self, metadata: Dict[str, any], inputs) -> None:
        self.metadata = metadata
        self.inputs = inputs
        self.parquet_path = Path("tests/data/minute_ad_events.parquet")

    def get_validated_data(self) -> pd.DataFrame:
        metric_def = self.metadata["metrics"].get("minute_ad_events.impressions")
        if not metric_def:
            raise ValueError("Metric not found in metadata")
        if self.inputs.dimension not in metric_def.get("dimensions", []):
            raise ValueError(f"Invalid dimension: {self.inputs.dimension}")

        conn = duckdb.connect()
        query = f"""
            SELECT country, SUM(impressions) AS impressions
            FROM read_parquet('{self.parquet_path.as_posix()}')
            GROUP BY country
        """
        df = conn.execute(query).df()
        if self.inputs.countries:
            df = df[df["country"].isin(self.inputs.countries)]
        if self.inputs.include_total:
            total = pd.DataFrame({"country": ["total"], "impressions": [df["impressions"].sum()]})
            df = pd.concat([df, total], ignore_index=True)
        return df

    def get_metric_overview_from_dbt(self, table: str = "mart_hourly_campaign_performance") -> pd.DataFrame:
        """Query dbt.duckdb for a simple country rollup as a demo.

        This method enables replacing the demo parquet with modeled data
        produced by dbt. It intentionally mirrors the schema expected by
        QueryBuilder/tests (country, impressions).
        """
        db_path = Path("dbt_ads_project/dbt.duckdb")
        con = duckdb.connect(db_path.as_posix())
        query = f"""
            SELECT 'total'::TEXT AS country, SUM(impressions) AS impressions
            FROM {table}
        """
        return con.execute(query).df()

    def get_timeseries_from_dbt(
        self,
        metric: str = "impressions",
        days: int = 14,
        table: str = "mart_hourly_campaign_performance",
        time_column: str = "hour_ts",
        grain: str = "day",
    ) -> pd.DataFrame:
        """Return a simple timeseries over the last N days from dbt.duckdb.

        Produces columns: timestamp (ISO8601), country (label, set to 'total'), <metric>.
        """
        db_path = Path("dbt_ads_project/dbt.duckdb")
        con = duckdb.connect(db_path.as_posix())
        ts_expr = f"date_trunc('{grain}', {time_column})"
        query = f"""
            SELECT {ts_expr} AS timestamp, SUM({metric}) AS {metric}
            FROM {table}
            WHERE {time_column} >= now() - INTERVAL {days} DAY
            GROUP BY 1
            ORDER BY 1
        """
        df = con.execute(query).df()
        if not df.empty:
            # Ensure ISO8601 strings for timestamps expected by many renderers
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.strftime('%Y-%m-%dT%H:%M:%S')
            df["country"] = "total"
        return df
