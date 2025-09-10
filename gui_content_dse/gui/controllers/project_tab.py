from __future__ import annotations

from pathlib import Path

from ..models import Project
from ..views.tabs import CampaignPerformanceView


class ProjectTab:
    """Controller for an open project.

    Each tab holds its own :class:`Project` state.
    """

    def __init__(self, project_path: Path) -> None:
        self.project = Project(name=project_path.stem, path=project_path)
        self._campaign_view: CampaignPerformanceView | None = None

    def load_campaign_csv(self, csv_path: Path) -> None:
        self.project.load_campaign_performance(csv_path)

    def campaign_view(self) -> CampaignPerformanceView:
        if self._campaign_view is None:
            self._campaign_view = CampaignPerformanceView(self.project)
        return self._campaign_view