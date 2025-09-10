# DearEIS is licensed under the GPLv3 or later (https://www.gnu.org/licenses/gpl-3.0.html).
# Copyright 2025 DearEIS developers
"""Data model and persistence utilities

Refactor recommendations:
- P0: Integrate with central registry for modular extension
- P1: Adopt dataclasses for immutable records
- P2: Isolate serialization/deserialization logic
- P2: Use factory functions for constructing data sets

Tests:
- tests/test_data_timeseries.py: assert registry integration and core behavior
- cover edge cases such as invalid inputs, empty data, missing registry entries, and unexpected state transitions
"""


from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple
import json
import csv

__all__ = ["parse_yaml_semantics", "load_csv", "TimeseriesDataset"]


def parse_yaml_semantics(path: Path) -> Tuple[str, List[str], Dict[str, str]]:
    """Return the time column, metric names and descriptions defined in a YAML file.

    The parser implements a minimal subset of YAML by first attempting to
    interpret the file as JSON.  If that fails a very small line based scan is
    used.  Only the pieces required by the tests are supported; the function is
    intentionally forgiving and returns empty defaults when parsing fails.
    """
    time_col = "hour_ts"
    metrics: List[str] = []
    descriptions: Dict[str, str] = {}
    if not path.exists():
        return time_col, metrics, descriptions

    try:
        data = json.loads(path.read_text())
        cols = data.get("seeds", [])[0].get("columns", [])
        for col in cols:
            name = col.get("name")
            if not name:
                continue
            if name == "hour_ts":
                time_col = name
            meta = col.get("meta", {})
            semantic = meta.get("semantic", {})
            if semantic.get("dimension", {}).get("is_metric_time"):
                time_col = name
            if "measure" in semantic:
                metrics.append(name)
                desc = col.get("description")
                if isinstance(desc, str):
                    descriptions[name] = desc
    except Exception:
        lines = path.read_text().splitlines()
        in_columns = False
        current_name = None
        current_desc = ""
        has_measure = False
        for line in lines:
            s = line.strip()
            if s.startswith("columns:"):
                in_columns = True
                continue
            if not in_columns:
                continue
            if s.startswith("- name:"):
                if current_name and has_measure:
                    metrics.append(current_name)
                    if current_desc:
                        descriptions[current_name] = current_desc
                current_name = s.split(":", 1)[1].strip()
                current_desc = ""
                has_measure = False
            elif "is_metric_time" in s or s.startswith("name: hour_ts"):
                time_col = current_name or "hour_ts"
            elif s.startswith("description:"):
                current_desc = s.split(":", 1)[1].strip()
            elif "measure:" in s:
                has_measure = True
        if current_name and has_measure:
            metrics.append(current_name)
            if current_desc:
                descriptions[current_name] = current_desc

    return time_col, metrics, descriptions


def load_csv(path: Path, time_col: str, metric: str) -> List[Tuple[float, float]]:
    """Load a CSV file containing timeseries data.

    The time column is currently ignored and the row index is used instead in
    order to avoid a heavy dependency on datetime parsing.
    """
    if not path.exists():
        return []
    data: List[Tuple[float, float]] = []
    with path.open(newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            t_val = row.get(time_col)
            y_val = row.get(metric)
            if t_val is None or y_val is None:
                continue
            try:
                y = float(y_val)
            except Exception:
                continue
            data.append((float(len(data)), y))
    return data


@dataclass
class TimeseriesDataset:
    """Container for campaign performance timeseries data.

    Parameters are intentionally lightweight and only cover the pieces required
    by the GUI tab and example scripts.  The class lazily loads metrics from the
    CSV file on demand so that large data sets remain inexpensive to
    instantiate.
    """

    csv_path: Path
    yaml_path: Path
    time_column: str = "hour_ts"
    metrics: List[str] = field(default_factory=list)
    metric_descriptions: Dict[str, str] = field(default_factory=dict)
    _cache: Dict[str, List[Tuple[float, float]]] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        time_col, metrics, desc = parse_yaml_semantics(self.yaml_path)
        if time_col:
            self.time_column = time_col
        if metrics:
            self.metrics = metrics
        if desc:
            self.metric_descriptions = desc

    def load_metric(self, metric: str) -> List[Tuple[float, float]]:
        """Return timeseries data for *metric*.

        Results are cached after the first load to avoid repeatedly reading the
        CSV file.
        """

        if metric not in self._cache:
            self._cache[metric] = load_csv(self.csv_path, self.time_column, metric)
        return self._cache[metric]
