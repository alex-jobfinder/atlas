from __future__ import annotations

from typing import Callable


class OverviewView:
    """Landing page for loading projects."""

    def __init__(self, open_callback: Callable[[str], None]) -> None:
        self.open_callback = open_callback

    def show(self) -> None:
        import dearpygui.dearpygui as dpg

        with dpg.window(label="Overview"):
            dpg.add_text("Content DSE @ Netflix")
            dpg.add_input_text(label="Project path", tag="project_path")
            dpg.add_button(label="Open Project", callback=self._open_project)

    def _open_project(self) -> None:
        import dearpygui.dearpygui as dpg

        path = dpg.get_value("project_path")
        self.open_callback(path)