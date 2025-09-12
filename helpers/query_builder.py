from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd

class QueryBuilder:
    """Constructs a minimal representation of an ASL query."""

    def __init__(self, data: pd.DataFrame, inputs) -> None:
        self.data = data
        self.inputs = inputs

    def build_asl(self) -> Dict[str, Any]:
        label_col = getattr(self.inputs, "dimension", "country")
        value_col = getattr(self.inputs, "metric", "impressions")

        if label_col not in self.data.columns:
            raise KeyError(f"Dimension column not found in DataFrame: {label_col}")
        if value_col not in self.data.columns:
            raise KeyError(f"Metric column not found in DataFrame: {value_col}")

        expressions: List[Dict[str, Any]] = []
        for _, row in self.data.iterrows():
            expressions.append({"label": row[label_col], "value": row[value_col]})
        if not expressions:
            raise ValueError("No expressions generated")
        return {"metric": value_col, "dimension": label_col, "expressions": expressions}

    def build_time_asl(self) -> Dict[str, Any]:
        """Build ASL payload for time series data.

        Expects columns: timestamp, <metric>. Labels will use timestamp.
        """
        value_col = getattr(self.inputs, "metric", "impressions")
        if "timestamp" not in self.data.columns:
            raise KeyError("timestamp column not found in DataFrame")
        if value_col not in self.data.columns:
            raise KeyError(f"Metric column not found in DataFrame: {value_col}")
        expressions: List[Dict[str, Any]] = []
        for _, row in self.data.iterrows():
            expressions.append({
                "label": row["timestamp"],
                "value": row[value_col],
            })
        if not expressions:
            raise ValueError("No expressions generated")
        return {"metric": value_col, "dimension": "timestamp", "expressions": expressions}
