from __future__ import annotations

from pathlib import Path
from typing import Dict

from .project_tab import ProjectTab
from ..views.tabs import OverviewView


class ProgramWindow:
    """Top-level application controller managing project tabs."""

    def __init__(self) -> None:
        self._projects: Dict[str, ProjectTab] = {}
        # Overview view is built lazily
        self._overview: OverviewView | None = None

    def open_project(self, project_path: Path) -> ProjectTab:
        """Open a project and return its controller."""
        tab = ProjectTab(project_path)
        self._projects[project_path.as_posix()] = tab
        return tab

    def get_project(self, project_path: Path) -> ProjectTab:
        return self._projects[project_path.as_posix()]

    def overview_view(self) -> OverviewView:
        """Return the landing view for opening projects."""
        if self._overview is None:
            self._overview = OverviewView(
                open_callback=lambda p: self.open_project(Path(p))
            )
        return self._overview