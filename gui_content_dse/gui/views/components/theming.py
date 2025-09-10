from __future__ import annotations

from typing import List, Tuple
import dearpygui.dearpygui as dpg


def build_global_theme() -> int:
    with dpg.theme() as global_theme:
        with dpg.theme_component(dpg.mvAll):
            for var in (
                dpg.mvStyleVar_WindowRounding,
                dpg.mvStyleVar_ChildRounding,
                dpg.mvStyleVar_FrameRounding,
                dpg.mvStyleVar_PopupRounding,
                dpg.mvStyleVar_ScrollbarRounding,
                dpg.mvStyleVar_GrabRounding,
                dpg.mvStyleVar_TabRounding,
            ):
                dpg.add_theme_style(var, 2.0, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvPlotStyleVar_PlotPadding, 8, 8, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LabelPadding, 5, 2, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LegendPadding, 5, 5, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LegendInnerPadding, 4, 4, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_MousePosPadding, 8, 8, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_LineWeight, 1.5, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 4.5, category=dpg.mvThemeCat_Plots)
            dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerWeight, 2.0, category=dpg.mvThemeCat_Plots)
    return global_theme


def build_plot_theme() -> int:
    with dpg.theme() as plot_theme:
        with dpg.theme_component(dpg.mvAll):
            dpg.add_theme_color(dpg.mvPlotCol_FrameBg, [255.0, 255.0, 255.0, 0.0], category=dpg.mvThemeCat_Plots)
    return plot_theme


def vibrant_colors() -> List[Tuple[float, float, float, float]]:
    return [
        (0.0, 119.0, 187.0, 255.0),
        (0.0, 153.0, 136.0, 255.0),
        (238.0, 119.0, 51.0, 255.0),
        (238.0, 51.0, 119.0, 255.0),
        (204.0, 51.0, 17.0, 255.0),
        (187.0, 187.0, 187.0, 255.0),
        (51.0, 187.0, 238.0, 255.0),
    ]


def create_line_theme(color: Tuple[float, float, float, float]) -> int:
    with dpg.theme() as t:
        with dpg.theme_component(dpg.mvLineSeries):
            dpg.add_theme_color(dpg.mvPlotCol_Line, color, category=dpg.mvThemeCat_Plots)
    return t

