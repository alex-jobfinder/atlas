from __future__ import annotations

from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

from .campaign import CampaignMetric


class Project(BaseModel):
    """Container for all project state.

    Projects are identified by a name and hold campaign performance data.
    """

    name: str
    path: Path
    campaign_metrics: List[CampaignMetric] = Field(default_factory=list)

    def load_campaign_performance(self, csv_path: Path) -> None:
        """Populate :attr:`campaign_metrics` from a CSV file."""
        import csv

        with csv_path.open(newline="") as fh:
            reader = csv.DictReader(fh)
            self.campaign_metrics = [
                CampaignMetric(
                    campaign_id=row["campaign_id"],
                    impressions=int(row["impressions"]),
                    clicks=int(row["clicks"]),
                    spend=float(row["spend"]),
                )
                for row in reader
            ]