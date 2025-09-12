import json
from pathlib import Path
from enum import Enum
from typing import Dict, Tuple, Type

class ManifestParser:
    """Parses project manifests and exposes metadata and dynamic enums.

    Supports:
      - Simple demo manifest (manifest.json)
      - dbt semantic manifest (dbt_ads_project/target/semantic_manifest.json)
    """

    def __init__(
        self,
        manifest_path: Path | str = "manifest.json",
        semantic_manifest_path: Path | str = "dbt_ads_project/target/semantic_manifest.json",
    ) -> None:
        self.manifest_path = Path(manifest_path)
        self.semantic_manifest_path = Path(semantic_manifest_path)

    def parse(
        self,
        prefer_semantic: bool = False,
    ) -> Tuple[Dict[str, any], Type[Enum], Type[Enum], Type[Enum]]:
        if prefer_semantic and self.semantic_manifest_path.exists():
            return self._parse_semantic_manifest()
        else:
            return self._parse_demo_manifest()

    def _parse_demo_manifest(self) -> Tuple[Dict[str, any], Type[Enum], Type[Enum], Type[Enum]]:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest file not found: {self.manifest_path}")
        with self.manifest_path.open() as f:
            data = json.load(f)
        metrics = data.get("metrics", {})
        if not metrics:
            raise ValueError("No metrics found in manifest")

        metric_names = {m.split(".")[-1].upper(): m for m in metrics.keys()}
        MetricEnum = Enum("MetricEnum", metric_names)

        first_metric = next(iter(metrics.values()))
        dims = {d.upper(): d for d in first_metric.get("dimensions", [])}
        DimensionEnum = Enum("DimensionEnum", dims)

        agg = first_metric.get("aggregation", "sum")
        AggregationEnum = Enum("AggregationEnum", {agg.upper(): agg})

        metadata = {"metrics": metrics}
        return metadata, MetricEnum, DimensionEnum, AggregationEnum

    def _parse_semantic_manifest(self) -> Tuple[Dict[str, any], Type[Enum], Type[Enum], Type[Enum]]:
        with self.semantic_manifest_path.open() as f:
            data = json.load(f)

        # Collect metrics from semantic manifest
        metrics_list = data.get("metrics", [])
        if not metrics_list:
            raise ValueError("No metrics found in semantic_manifest.json")

        # Build a simplified mapping: metric_name -> {aggregation, dimensions}
        # Dimensions include time proxy (metric_time) and any primary entity dims (campaign)
        # plus semantic model dims where sensible.
        dims_from_models: Dict[str, set] = {}
        for sm in data.get("semantic_models", []):
            # time dims map to metric_time dunders in MetricFlow; expose a canonical metric_time key
            time_dims = {"metric_time"}
            cat_dims = {d.get("name") for d in sm.get("dimensions", []) if d.get("type") == "categorical"}
            entity_names = {e.get("name") for e in sm.get("entities", []) if e.get("type") in {"primary", "foreign"}}
            dims_from_models[sm.get("name", "")] = time_dims.union(cat_dims).union(entity_names)

        metrics: Dict[str, Dict[str, any]] = {}
        for m in metrics_list:
            name = m.get("name")
            agg = m.get("type")  # simple/ratio/etc; fall back to type_params/measure.agg where needed
            # Use all dims from first semantic model for now (single-fact project)
            all_model_dims = set()
            for sm_dims in dims_from_models.values():
                all_model_dims |= sm_dims
            metrics[name] = {
                "aggregation": agg or "sum",
                "dimensions": sorted(d for d in all_model_dims if d),
            }

        MetricEnum = Enum("MetricEnum", {n.upper(): n for n in metrics.keys()})
        # Use union of all dims for DimensionEnum
        all_dims = set()
        for v in metrics.values():
            all_dims.update(v.get("dimensions", []))
        DimensionEnum = Enum("DimensionEnum", {d.upper(): d for d in sorted(all_dims)})
        AggregationEnum = Enum("AggregationEnum", {"SUM": "sum"})

        metadata = {"metrics": metrics}
        return metadata, MetricEnum, DimensionEnum, AggregationEnum
