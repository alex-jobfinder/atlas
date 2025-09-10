from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import dearpygui.dearpygui as dpg

from gui_content_dse.gui.models.timeseries import (
    parse_yaml_semantics,
    build_campaign_dataset,
)
from gui_content_dse.gui.views.components.theming import (
    build_global_theme,
    build_plot_theme,
    vibrant_colors,
    create_line_theme,
)


class CampaignPerformanceController:
    """Controller for the Campaign Performance tab.

    Exposes the same attributes used by tests for backward compatibility.
    """

    def __init__(self):
        # GUI handles
        self._sidebar_width: int = 320
        self._sidebar: Optional[int] = None
        self._metric_combo: Optional[int] = None
        self._time_input: Optional[int] = None
        self._csv_input: Optional[int] = None
        self._yaml_input: Optional[int] = None
        self._plot: Optional[int] = None
        self._x_axis: Optional[int] = None
        self._y_axis: Optional[int] = None
        self._series_tag: Optional[int] = None
        self._series_tags: Dict[str, int] = {}

        # State
        self._metrics: List[str] = []
        self._metric_map: Dict[str, str] = {}
        self._current_metric: Optional[str] = None
        self._metric_descriptions: Dict[str, str] = {}
        self._metric_aggs: Dict[str, str] = {}
        self._campaigns: List[str] = []
        self._index_labels: List[str] = []
        self._times_by_campaign: Dict[str, List[float]] = {}
        self._series_by_campaign: Dict[str, Dict[str, List[float]]] = {}
        self._current_yaml_path: Optional[Path] = None

        # Themes (built after DPG context is created)
        self._global_theme: Optional[int] = None
        self._plot_theme: Optional[int] = None
        self._vibrant_colors: List[Tuple[float, float, float, float]] = []

    def setup_themes(self):
        self._global_theme = build_global_theme()
        self._plot_theme = build_plot_theme()
        self._vibrant_colors = vibrant_colors()

    # ---------- UI build ----------
    def build_ui(self):
        with dpg.group(horizontal=True):
            self._create_sidebar()
            self._create_plot()
        self._autoload_defaults()

    def _create_sidebar(self):
        self._sidebar = dpg.add_child_window(border=False, width=self._sidebar_width, height=-1)

        dpg.add_text("Campaign", parent=self._sidebar)
        self._campaign_combo = dpg.add_combo(
            items=["All"], width=-1, parent=self._sidebar, default_value="All",
            callback=lambda s, a, u: self._on_campaign_change(a)
        )

        dpg.add_spacer(height=8, parent=self._sidebar)
        dpg.add_text("Metric", parent=self._sidebar)
        self._metric_combo = dpg.add_combo(
            items=[], width=-1, parent=self._sidebar,
            callback=lambda s, a, u: self._on_metric_change(a)
        )
        dpg.add_spacer(height=4, parent=self._sidebar)
        with dpg.collapsing_header(label="Metric Info", default_open=False, parent=self._sidebar):
            self._metric_desc_text = dpg.add_text("Description: —")
            self._metric_agg_text = dpg.add_text("Aggregation: —")
            dpg.add_spacer(height=4)
            dpg.add_text("Metric YAML")
            self._metric_yaml_text = dpg.add_input_text(
                multiline=True, readonly=True, width=-1, height=220, default_value="—"
            )

        dpg.add_spacer(height=8, parent=self._sidebar)
        dpg.add_text("Time Column", parent=self._sidebar)
        self._time_input = dpg.add_input_text(default_value="hour_ts", width=-1, parent=self._sidebar)

        dpg.add_spacer(height=4, parent=self._sidebar)
        dpg.add_text("CSV Path", parent=self._sidebar)
        self._csv_input = dpg.add_input_text(
            width=-1, parent=self._sidebar, tag="campaign_csv_path",
            default_value=str(Path("gui_content_dse/data/full/campaign_performance.csv"))
        )

        dpg.add_spacer(height=4, parent=self._sidebar)
        dpg.add_text("YAML Path (optional)", parent=self._sidebar)
        self._yaml_input = dpg.add_input_text(
            width=-1, parent=self._sidebar,
            default_value=str(Path("gui_content_dse/data/full/campaign_performance.yml"))
        )

        dpg.add_button(label="Load", parent=self._sidebar, callback=lambda: self._load_and_render())

    def _create_plot(self):
        self._plot = dpg.add_plot(crosshairs=True, width=-1, height=-1)
        if self._plot_theme is None:
            self.setup_themes()
        dpg.bind_item_theme(self._plot, self._plot_theme)
        self._x_axis = dpg.add_plot_axis(dpg.mvXAxis, label="time", parent=self._plot)
        self._y_axis = dpg.add_plot_axis(dpg.mvYAxis, label="metric", parent=self._plot)

    # ---------- Actions ----------
    def _open_campaign_csv_dialog(self):
        dpg.focus_item("campaign_csv_path")

    def _show_about(self):
        with dpg.window(label="About", modal=True, width=420, height=220):
            dpg.add_text("Content DSE - Campaign Performance")
            dpg.add_text("Version 0.1.0")
            dpg.add_separator()
            dpg.add_text("Built with Dear PyGui")
            dpg.add_text("Tabbed UI similar to DearEIS")
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item(dpg.last_item()))

    # ---------- Data load & render ----------
    def _load_and_render(self):
        csv_path = Path(dpg.get_value(self._csv_input) or "").expanduser()
        yaml_path = Path(dpg.get_value(self._yaml_input) or "").expanduser()
        self._current_yaml_path = yaml_path if yaml_path.exists() else None
        time_col = (dpg.get_value(self._time_input) or "hour_ts").strip()
        if not csv_path.exists():
            return

        # Read rows
        rows: List[Dict[str, str]] = []
        with csv_path.open("r", newline="") as f:
            reader = csv.DictReader(f)
            rows.extend(reader)
        if not rows:
            return

        columns = list(rows[0].keys())
        # Build dataset
        dataset = build_campaign_dataset(rows, columns, yaml_path if yaml_path.exists() else None, time_col)
        self._metrics = dataset.metrics
        self._metric_descriptions = dataset.metric_descriptions
        self._metric_aggs = dataset.metric_aggs
        self._campaigns = dataset.campaigns
        self._index_labels = dataset.index_labels
        self._times_by_campaign = dataset.times_by_campaign
        self._series_by_campaign = dataset.series_by_campaign

        # Update UI
        self._metric_map = {m: m for m in self._metrics}
        dpg.configure_item(self._metric_combo, items=list(self._metrics))
        dpg.configure_item(self._campaign_combo, items=["All", "All (aggregate)"] + self._campaigns)
        if self._metrics:
            default_metric = self._metrics[0]
            dpg.set_value(self._metric_combo, default_metric)
            dpg.configure_item(self._y_axis, label=default_metric)
            self._current_metric = default_metric
            self._update_metric_details(default_metric)
        if self._campaigns:
            dpg.set_value(self._campaign_combo, "All (aggregate)")

        self._render_series()

    def _autoload_defaults(self):
        try:
            csv_path = Path(dpg.get_value(self._csv_input) or "")
            if csv_path.exists():
                self._load_and_render()
        except Exception:
            pass

    # ---------- Rendering helpers ----------
    def _on_metric_change(self, display: str):
        metric = self._metric_map.get(display, display)
        if not metric:
            return
        self._current_metric = metric
        dpg.configure_item(self._y_axis, label=display)
        self._update_metric_details(metric)
        self._render_series()

    def _on_campaign_change(self, display: str):
        self._render_series()

    def _render_series(self):
        # Clear previous
        if getattr(self, "_series_tag", None) is not None and dpg.does_item_exist(self._series_tag):
            try:
                dpg.delete_item(self._series_tag)
            except Exception:
                pass
            self._series_tag = None
        for tag in list(getattr(self, "_series_tags", {}).values()):
            if dpg.does_item_exist(tag):
                try:
                    dpg.delete_item(tag)
                except Exception:
                    pass
        self._series_tags = {}

        metric = getattr(self, "_current_metric", None)
        if not metric:
            return

        selected = dpg.get_value(self._campaign_combo) if hasattr(self, "_campaign_combo") else "All"
        campaigns = self._campaigns if selected == "All" else [selected]
        palette = self._vibrant_colors

        if selected == "All (aggregate)":
            xs = list(range(len(self._index_labels)))
            agg_name = self._metric_aggs.get(metric, "sum").lower()
            ys: List[float] = []
            for x in xs:
                vals: List[float] = []
                for cid in self._campaigns:
                    series_x = self._times_by_campaign.get(cid, [])
                    try:
                        i = series_x.index(x)
                        vals.append(self._series_by_campaign.get(cid, {}).get(metric, [])[i])
                    except ValueError:
                        continue
                if not vals:
                    ys.append(0.0)
                else:
                    ys.append(sum(vals) if agg_name == "sum" else (sum(vals) / len(vals)))

            label = f"All ({agg_name})"
            tag = dpg.add_line_series(xs, ys, parent=self._y_axis, label=label)
            self._series_tags[label] = tag
            self._series_tag = tag
            try:
                dpg.bind_item_theme(tag, create_line_theme(palette[0]))
            except Exception:
                pass
            self._update_time_ticks(xs)
        else:
            longest_xs: List[float] = []
            for idx, cid in enumerate(campaigns):
                xs = self._times_by_campaign.get(cid, [])
                ys = self._series_by_campaign.get(cid, {}).get(metric, [])
                if not xs or not ys:
                    continue
                tag = dpg.add_line_series(xs, ys, parent=self._y_axis, label=str(cid))
                self._series_tags[cid] = tag
                self._series_tag = tag
                longest_xs = xs if len(xs) > len(longest_xs) else longest_xs
                try:
                    dpg.bind_item_theme(tag, create_line_theme(palette[idx % len(palette)]))
                except Exception:
                    pass
            self._update_time_ticks(longest_xs)

        try:
            if hasattr(dpg, "fit_axis_data"):
                dpg.fit_axis_data(self._x_axis)
                dpg.fit_axis_data(self._y_axis)
        except Exception:
            pass

    def _update_metric_details(self, metric: str):
        description = self._metric_descriptions.get(metric, "—")
        agg = self._metric_aggs.get(metric, "—")
        try:
            dpg.set_value(self._metric_desc_text, f"Description: {description}")
            dpg.set_value(self._metric_agg_text, f"Aggregation: {agg}")
            yaml_block = "—"
            if self._current_yaml_path:
                yaml_block = self._extract_yaml_block(self._current_yaml_path, metric) or "—"
            dpg.set_value(self._metric_yaml_text, yaml_block)
        except Exception:
            pass

    def _extract_yaml_block(self, path: Path, metric: str) -> str:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            return ""
        lines = text.splitlines()
        start = -1
        start_indent = 0
        for i, line in enumerate(lines):
            s = line.strip()
            if s.startswith("- name:"):
                name = s.split(":", 1)[1].strip()
                if name == metric:
                    start = i
                    start_indent = len(line) - len(line.lstrip())
                    break
        if start < 0:
            return ""
        j = start + 1
        while j < len(lines):
            line = lines[j]
            s = line.strip()
            indent = len(line) - len(line.lstrip())
            if s.startswith("- name:") and indent == start_indent:
                break
            j += 1
        return "\n".join(lines[start:j])

    # ---------- Layout ----------
    def _update_time_ticks(self, xs: List[float]):
        try:
            if not xs:
                return
            plot_w = int(dpg.get_item_width(self._plot)) if self._plot else 800
            # Default labels from index
            px_per_label = 110
            max_ticks = max(2, min(12, plot_w // px_per_label))
            n = len(xs)
            step = max(1, (n + max_ticks - 1) // max_ticks)
            tick_positions = [xs[i] for i in range(0, n, step)]
            labels: List[str] = []
            for pos in tick_positions:
                i = int(pos)
                labels.append(self._index_labels[i] if 0 <= i < len(self._index_labels) else str(i))
            ticks = list(zip(tick_positions, labels))
            if hasattr(dpg, "set_axis_ticks"):
                dpg.set_axis_ticks(self._x_axis, ticks)
        except Exception:
            pass

    def _on_resize(self):
        try:
            width = dpg.get_viewport_client_width()
            height = dpg.get_viewport_client_height()
        except Exception:
            return
        if self._sidebar and dpg.does_item_exist(self._sidebar):
            try:
                dpg.configure_item(self._sidebar, width=self._sidebar_width, height=max(100, height - 64))
            except Exception:
                pass
        plot_width = max(200, width - self._sidebar_width - 40)
        plot_height = max(200, height - 64)
        if self._plot and dpg.does_item_exist(self._plot):
            try:
                dpg.configure_item(self._plot, width=plot_width, height=plot_height)
            except Exception:
                pass
