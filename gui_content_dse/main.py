#!/usr/bin/env python3
"""
Content DSE GUI - Minimal Tabbed App

This entry point initializes a simple Dear PyGui application with a
top tab bar, starting with a "Campaign Performance" tab. Project-related
code has been removed to focus on a single, self-contained workflow.
The Campaign Performance tab mirrors DearEIS' Timeseries tab UX: a left
sidebar for filters (campaign, metric, sources) and a right plot area
with themed styling and responsive sizing.
"""

import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

import dearpygui.dearpygui as dpg
try:
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
    from gui_content_dse.gui.views.components.plot import set_time_ticks
except ModuleNotFoundError:
    # Allow running as `python gui_content_dse/main.py` by patching sys.path
    import os, sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
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
    from gui_content_dse.gui.views.components.plot import set_time_ticks

 



from gui_content_dse.gui.controllers.campaign_performance import CampaignPerformanceController
from gui_content_dse.gui.views.tabs.campaign_performance import CampaignPerformanceView


class ContentDSEApp:
    """Slim app shell that wires DearPyGui + tabs.

    Attributes/methods delegate to the CampaignPerformanceController for
    backward compatibility with existing tests.
    """

    def __init__(self):
        self.controller = CampaignPerformanceController()

    # --- lifecycle helpers for testing ---
    def init(self, show_viewport: bool = True):
        """Initialize DearPyGui without entering the main loop.

        Set show_viewport=False for headless test environments.
        """
        dpg.create_context()
        # Global app config and anti-aliasing similar to DearEIS
        try:
            dpg.configure_app(anti_aliased_lines=True, anti_aliased_fill=True)
        except Exception:
            # Some DearPyGui builds don't expose these kwargs; ignore gracefully
            pass
        dpg.create_viewport(title="Content DSE - Campaign Performance", width=1280, height=800)

        # Build and bind global theme from controller
        self.controller.setup_themes()
        dpg.bind_theme(self.controller._global_theme)

        self._create_main_window()
        dpg.setup_dearpygui()
        if show_viewport:
            dpg.show_viewport()
        # Ensure initial size is applied
        self._on_resize()

    def frame(self, frames: int = 1):
        """Render a specific number of frames (no-op if viewport not shown)."""
        for _ in range(max(0, frames)):
            if dpg.is_dearpygui_running():
                dpg.render_dearpygui_frame()

    def shutdown(self):
        """Destroy DearPyGui context (safe to call multiple times)."""
        try:
            dpg.destroy_context()
        except Exception:
            pass

    def run(self):
        self.init(show_viewport=True)
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()
        self.shutdown()

    # Delegate attrs/methods to controller for backward compatibility
    def __getattr__(self, name):
        try:
            return getattr(self.controller, name)
        except AttributeError:
            raise

    def _create_main_window(self):
        with dpg.window(label="Content DSE", width=-1, height=-1, tag="main_window"):
            # Menu bar with basic actions
            with dpg.menu_bar():
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Load Campaign CSV...", callback=self.controller._open_campaign_csv_dialog)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

                with dpg.menu(label="Help"):
                    dpg.add_menu_item(label="About", callback=self.controller._show_about)

            # Top tab bar similar to DearEIS; start with Campaign Performance
            with dpg.tab_bar(tag="main_tab_bar"):
                with dpg.tab(label="Campaign Performance", tag="campaign_performance_tab"):
                    # Build the tab via controller/view
                    CampaignPerformanceView(self.controller).build()
        # Resize handler (aligns with DearEIS philosophy of responsive panels)
        try:
            with dpg.handler_registry():
                if hasattr(dpg, "add_viewport_resize_handler"):
                    dpg.add_viewport_resize_handler(callback=lambda s, a: self.controller._on_resize())
        except Exception:
            # Older DearPyGui versions may not support this handler; ignore
            pass

    def _create_campaign_performance_tab(self):
        # Tab is built within _create_main_window via the view
        pass

    # ===== Campaign Timeseries Sidebar =====
    def _create_campaign_sidebar(self):
        self.controller._create_sidebar()

        # Campaign filter
        dpg.add_text("Campaign", parent=self._sidebar)
        self._campaign_combo = dpg.add_combo(items=["All"], width=-1, parent=self._sidebar,
                                             default_value="All",
                                             callback=lambda s, a, u: self._on_campaign_change(a))

        dpg.add_spacer(height=8, parent=self._sidebar)
        dpg.add_text("Metric", parent=self._sidebar)
        self._metric_combo = dpg.add_combo(items=[], width=-1, parent=self._sidebar,
                                           callback=lambda s, a, u: self._on_metric_change(a))
        dpg.add_spacer(height=4, parent=self._sidebar)
        with dpg.collapsing_header(label="Metric Info", default_open=False, parent=self._sidebar):
            self._metric_desc_text = dpg.add_text("Description: —")
            self._metric_agg_text = dpg.add_text("Aggregation: —")
            dpg.add_spacer(height=4)
            dpg.add_text("Metric YAML")
            self._metric_yaml_text = dpg.add_input_text(multiline=True, readonly=True, width=-1, height=220,
                                                        default_value="—")

        dpg.add_spacer(height=8, parent=self._sidebar)
        dpg.add_text("Time Column", parent=self._sidebar)
        # Default to full dataset paths; tests or users can override in the input
        default_csv = Path("/home/alex/fastapi-template/gui_content_dse/data/full/campaign_performance.csv")
        default_yaml = Path("/home/alex/fastapi-template/gui_content_dse/data/full/campaign_performance.yml")

        # Use common column name from YAML semantics
        self._time_input = dpg.add_input_text(default_value="hour_ts", width=-1, parent=self._sidebar)

        dpg.add_spacer(height=4, parent=self._sidebar)
        dpg.add_text("CSV Path", parent=self._sidebar)
        self._csv_input = dpg.add_input_text(width=-1, parent=self._sidebar, tag="campaign_csv_path",
                                             default_value=str(default_csv))

        dpg.add_spacer(height=4, parent=self._sidebar)
        dpg.add_text("YAML Path (optional)", parent=self._sidebar)
        self._yaml_input = dpg.add_input_text(width=-1, parent=self._sidebar,
                                              default_value=str(default_yaml))

        dpg.add_button(label="Load", parent=self._sidebar, callback=lambda: self._load_and_render())

    def _open_campaign_csv_dialog(self):
        # Minimal placeholder: focus the input field to paste a path
        dpg.focus_item("campaign_csv_path")

    # ===== Campaign Timeseries Plot =====
    def _create_campaign_plot(self):
        self.controller._create_plot()

    # ===== Data Loading & Rendering (timeseries-like) =====
    def _load_and_render(self):
        # Delegate to controller
        self.controller._load_and_render()

    def _autoload_defaults(self):
        try:
            csv_path = Path(dpg.get_value(self._csv_input) or "")
            if csv_path.exists():
                self._load_and_render()
        except Exception:
            pass

    def _on_metric_change(self, display: str):
        self.controller._on_metric_change(display)

    def _update_metric_details(self, metric: str):
        self.controller._update_metric_details(metric)

    def _extract_yaml_block(self, path: Path, metric: str) -> str:
        return self.controller._extract_yaml_block(path, metric)

    def _on_campaign_change(self, display: str):
        self.controller._on_campaign_change(display)

    def _render_series(self):
        self.controller._render_series()

    def _update_time_ticks(self, xs: List[float]):
        """Set x-axis ticks using global index -> 'YYYY-MM-DD:HH' labels.
        Dynamically reduces tick count to avoid overlap.
        """
        try:
            if not xs:
                return
            n = len(xs)
            # Estimate available width and derive max tick count
            try:
                plot_w = int(dpg.get_item_width(self._plot))
                if plot_w <= 0:
                    raise ValueError
            except Exception:
                plot_w = max(600, dpg.get_viewport_client_width() - getattr(self, "_sidebar_width", 320) - 40)
            # Delegate to controller
            plot_w = int(dpg.get_item_width(self.controller._plot)) if self.controller._plot else 800
            from gui_content_dse.gui.views.components.plot import set_time_ticks
            set_time_ticks(self.controller._x_axis, xs, getattr(self.controller, "_index_labels", []), plot_w, self.controller._sidebar_width)
        except Exception:
            pass

    # ===== Theming & Layout =====
    def _build_themes(self):
        # Controlled by controller; nothing to do here
        pass

    def _create_series_theme(self, color: Tuple[float, float, float, float]) -> int:
        return create_line_theme(color)

    def _on_resize(self):
        try:
            width = dpg.get_viewport_client_width()
            height = dpg.get_viewport_client_height()
        except Exception:
            return
        # Sidebar height and plot size
        if getattr(self.controller, "_sidebar", None):
            try:
                dpg.configure_item(self.controller._sidebar, width=self.controller._sidebar_width, height=max(100, height - 64))
            except Exception:
                pass
        plot_width = max(200, width - self.controller._sidebar_width - 40)
        plot_height = max(200, height - 64)
        if getattr(self.controller, "_plot", None):
            try:
                dpg.configure_item(self.controller._plot, width=plot_width, height=plot_height)
            except Exception:
                pass

    # ===== UI Dialogs =====
    def _show_about(self):
        with dpg.window(label="About", modal=True, width=420, height=220):
            dpg.add_text("Content DSE - Campaign Performance")
            dpg.add_text("Version 0.1.0")
            dpg.add_separator()
            dpg.add_text("Built with Dear PyGui")
            dpg.add_text("Tabbed UI similar to DearEIS")
            dpg.add_button(label="Close", callback=lambda: dpg.delete_item(dpg.last_item()))


def main():
    print("Starting Content DSE - Campaign Performance UI...")
    app = ContentDSEApp()
    app.run()


if __name__ == "__main__":
    main()
