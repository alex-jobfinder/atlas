import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Default path to the bundled sample dataset
DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "default_dataset.json"
)

def load_default_dataset(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the bundled default dataset from disk.

    Parameters
    ----------
    path:
        Optional path override. If None, the built-in dataset is used.
    """
    data_path = path or DEFAULT_DATASET_PATH
    with data_path.open("r") as f:
        return json.load(f)

def _parse_time(ts: Optional[str]) -> Optional[int]:
    """Convert an ISO timestamp to epoch milliseconds."""
    if isinstance(ts, str):
        try:
            return int(
                datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() * 1000
            )
        except Exception:
            return None
    return ts

def format_dataset(sample_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform raw sample data into chart-friendly structure."""
    time_series: List[Dict[str, Any]] = []
    for plot in sample_data.get("plots", []):
        for line in plot.get("lines", []):
            line_data = line.get("data", {})
            ts = line_data.get("data", {})
            start = ts.get("startTime")
            if isinstance(start, str):
                start = datetime.fromisoformat(start.replace("Z", "+00:00")).timestamp() * 1000
            time_series.append(
                {
                    "tags": line_data.get("tags", {}),
                    "label": line_data.get("label", "Unknown"),
                    "data": {
                        "startTime": start,
                        "step": ts.get("step", 60000),
                        "values": ts.get("values", []),
                    },
                    "color": line.get("color", "#1f77b4"),
                    "line_width": line.get("lineWidth", 2),
                }
            )

    return {
        "time_series": time_series,
        "metadata": {
            "title": sample_data.get("title", "Default Dataset"),
            "start_time": _parse_time(sample_data.get("startTime")),
            "end_time": _parse_time(sample_data.get("endTime")),
            "step": sample_data.get("step", 60000),
            "source": "default_dataset",
        },
    }
