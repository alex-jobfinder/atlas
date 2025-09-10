from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json


def parse_yaml_semantics(path: Path) -> Tuple[str, List[str], Dict[str, str]]:
    """Return time column, metric names and descriptions from a YAML-like file.

    Implements a forgiving subset (tries JSON first, then a line-based scan).
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
            meta = col.get("meta", {})
            semantic = meta.get("semantic", {})
            if name == "hour_ts" or semantic.get("dimension", {}).get("is_metric_time"):
                time_col = name
            if "measure" in semantic:
                metrics.append(name)
                desc = col.get("description")
                if isinstance(desc, str):
                    descriptions[name] = desc
    except Exception:
        lines = path.read_text().splitlines()
        in_columns = False
        current_name: Optional[str] = None
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


@dataclass
class CampaignTimeseriesDataset:
    metrics: List[str]
    metric_descriptions: Dict[str, str]
    metric_aggs: Dict[str, str]
    campaigns: List[str]
    index_labels: List[str]
    times_by_campaign: Dict[str, List[float]]
    series_by_campaign: Dict[str, Dict[str, List[float]]]


def build_campaign_dataset(
    rows: List[Dict[str, str]],
    columns: List[str],
    yaml_path: Optional[Path],
    time_col: str,
) -> CampaignTimeseriesDataset:
    # YAML semantics
    yaml_time = None
    yaml_metrics: List[str] = []
    yaml_desc: Dict[str, str] = {}
    if yaml_path and yaml_path.exists():
        try:
            t_col, m_cols, desc = parse_yaml_semantics(yaml_path)
            yaml_time = t_col or None
            yaml_metrics = m_cols or []
            yaml_desc = desc or {}
        except Exception:
            pass
    if yaml_time and yaml_time in columns:
        time_col = yaml_time

    # campaign column
    campaign_col = "campaign_id" if "campaign_id" in columns else None

    # metric aggs
    metric_aggs: Dict[str, str] = {}
    metrics: List[str] = []
    if yaml_metrics and yaml_path and yaml_path.exists():
        try:
            import re
            lines = yaml_path.read_text(encoding="utf-8").splitlines()
            current: Optional[str] = None
            for line in lines:
                s = line.strip()
                if s.startswith("- name:"):
                    current = s.split(":", 1)[1].strip()
                elif "measure:" in s and "agg:" in s and current:
                    m = re.search(r"agg:\s*([A-Za-z_]+)", s)
                    if m:
                        metric_aggs[current] = m.group(1).lower()
        except Exception:
            metric_aggs = {}
        allowed = {"sum", "avg", "mean"}
        metrics = [m for m in yaml_metrics if m in columns and metric_aggs.get(m, "") in allowed]
    else:
        # Fallback: numeric inference
        for col in columns:
            if col == time_col:
                continue
            if campaign_col and col == campaign_col:
                continue
            good = 0
            for r in rows[:50]:
                try:
                    float(str(r.get(col, "")).replace(",", ""))
                    good += 1
                except Exception:
                    pass
            if good >= max(1, min(10, len(rows) // 4)):
                metrics.append(col)

    metrics = sorted(metrics)

    # Group rows by campaign
    groups: Dict[str, List[Dict[str, str]]] = {}
    if campaign_col:
        for r in rows:
            cid = str(r.get(campaign_col, "")).strip() or "(unknown)"
            groups.setdefault(cid, []).append(r)
    else:
        groups["All"] = rows

    # Build global index labels (YYYY-MM-DD:HH)
    def to_hour_label(raw: str) -> str:
        s = str(raw or "").strip()
        try:
            if s.endswith(" UTC"):
                s = s[:-4]
            fmt = "%Y-%m-%d %H:%M:%S.%f" if "." in s else "%Y-%m-%d %H:%M:%S"
            dt = datetime.strptime(s.replace("T", " "), fmt)
            return dt.strftime("%Y-%m-%d:%H")
        except Exception:
            try:
                date_part, time_part = s.split(" ", 1) if " " in s else s.split("T", 1)
                hour = time_part.split(":", 1)[0]
                return f"{date_part}:{hour}"
            except Exception:
                return s[:13].replace(" ", ":")

    all_keys: List[str] = []
    for items in groups.values():
        for r in items:
            all_keys.append(to_hour_label(r.get(time_col, "")))
    index_labels = sorted(set(all_keys))
    index_of = {k: i for i, k in enumerate(index_labels)}

    times_by_campaign: Dict[str, List[float]] = {}
    series_by_campaign: Dict[str, Dict[str, List[float]]] = {}

    for cid, items in groups.items():
        xs_idx: List[float] = []
        ys_map: Dict[str, List[float]] = {m: [] for m in metrics}
        for r in items:
            key = to_hour_label(r.get(time_col, ""))
            x = float(index_of.get(key, 0))
            xs_idx.append(x)
            for m in metrics:
                v = r.get(m, "")
                try:
                    ys_map[m].append(float(str(v).replace(",", "")))
                except Exception:
                    ys_map[m].append(0.0)
        times_by_campaign[cid] = xs_idx
        series_by_campaign[cid] = ys_map

    return CampaignTimeseriesDataset(
        metrics=metrics,
        metric_descriptions=yaml_desc,
        metric_aggs=metric_aggs,
        campaigns=sorted(groups.keys()),
        index_labels=index_labels,
        times_by_campaign=times_by_campaign,
        series_by_campaign=series_by_campaign,
    )

