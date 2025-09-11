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
