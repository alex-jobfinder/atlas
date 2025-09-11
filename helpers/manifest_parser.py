import json
from pathlib import Path
from enum import Enum
from typing import Dict, Tuple, Type

class ManifestParser:
    """Parses a dbt manifest.json and exposes metadata and dynamic enums."""

    def __init__(self, manifest_path: Path | str = "manifest.json") -> None:
        self.manifest_path = Path(manifest_path)

    def parse(self) -> Tuple[Dict[str, any], Type[Enum], Type[Enum], Type[Enum]]:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {self.manifest_path}")
        with self.manifest_path.open() as f:
            data = json.load(f)
        metrics = data.get("metrics", {})
        if not metrics:
            raise ValueError("No metrics found in manifest")

        # Build dynamic enums based on manifest content
        metric_names = {m.split(".")[-1].upper(): m for m in metrics.keys()}
        MetricEnum = Enum("MetricEnum", metric_names)

        first_metric = next(iter(metrics.values()))
        dims = {d.upper(): d for d in first_metric.get("dimensions", [])}
        DimensionEnum = Enum("DimensionEnum", dims)

        agg = first_metric.get("aggregation", "sum")
        AggregationEnum = Enum("AggregationEnum", {agg.upper(): agg})

        metadata = {"metrics": metrics}
        return metadata, MetricEnum, DimensionEnum, AggregationEnum
