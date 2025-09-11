from __future__ import annotations
import pandas as pd
from typing import Any, Dict

class QueryBuilder:
    """Constructs a minimal representation of an ASL query."""

    def __init__(self, data: pd.DataFrame, inputs) -> None:
        self.data = data
        self.inputs = inputs

    def build_asl(self) -> Dict[str, Any]:
        expressions = []
        for _, row in self.data.iterrows():
            expressions.append({"label": row["country"], "value": int(row["impressions"])})
        if not expressions:
            raise ValueError("No expressions generated")
        return {"chart": "line", "expressions": expressions}
