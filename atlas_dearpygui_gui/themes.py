"""
Simplified theme system for Atlas DearPyGui application
"""

import dearpygui.dearpygui as dpg


def create_light_theme():
    """Create a clean light theme."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # Core colors - light theme
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [242, 242, 242, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, [255, 255, 255, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, [250, 250, 250, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border, [178, 178, 178, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, [25, 25, 25, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [153, 153, 153, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [178, 178, 178, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [204, 204, 204, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, [178, 178, 178, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [204, 204, 204, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [230, 230, 230, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, [178, 178, 178, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, [204, 204, 204, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, [230, 230, 230, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [153, 153, 153, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [178, 178, 178, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, [153, 153, 153, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, [128, 128, 128, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, [178, 178, 178, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, [204, 204, 204, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, [51, 51, 51, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, [178, 178, 178, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, [178, 178, 178, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [204, 204, 204, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, [230, 230, 230, 255], category=dpg.mvThemeCat_Core)

            # Plot colors
            dpg.add_theme_color(dpg.mvThemeCol_PlotLines, [51, 51, 51, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, [25, 25, 25, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, [102, 102, 102, 255], category=dpg.mvThemeCat_Core)

            # Styles
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, category=dpg.mvThemeCat_Core)

    return theme


def create_dark_theme():
    """Create a clean dark theme."""
    with dpg.theme() as theme:
        with dpg.theme_component(dpg.mvAll):
            # Core colors - dark theme
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, [25, 25, 25, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, [40, 40, 40, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PopupBg, [50, 50, 50, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Border, [80, 80, 80, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Text, [230, 230, 230, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, [60, 60, 60, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, [80, 80, 80, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, [100, 100, 100, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, [70, 70, 70, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, [90, 90, 90, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, [110, 110, 110, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Header, [60, 60, 60, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, [80, 80, 80, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, [100, 100, 100, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBg, [40, 40, 40, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, [60, 60, 60, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, [40, 40, 40, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, [30, 30, 30, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrab, [80, 80, 80, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ScrollbarGrabHovered, [100, 100, 100, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_CheckMark, [200, 200, 200, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, [100, 100, 100, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Tab, [60, 60, 60, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabHovered, [80, 80, 80, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_TabActive, [100, 100, 100, 255], category=dpg.mvThemeCat_Core)

            # Plot colors
            dpg.add_theme_color(dpg.mvThemeCol_PlotLines, [200, 200, 200, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PlotLinesHovered, [255, 255, 255, 255], category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_PlotHistogram, [150, 150, 150, 255], category=dpg.mvThemeCat_Core)

            # Styles
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_PopupRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ScrollbarRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 3, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ButtonTextAlign, 0.5, category=dpg.mvThemeCat_Core)

    return theme


def apply_theme(theme_name: str):
    """Apply the specified theme."""
    if theme_name == "dark":
        theme = create_dark_theme()
    else:
        theme = create_light_theme()

    dpg.bind_theme(theme)
    return theme
