from __future__ import annotations

from typing import Sequence

from ...models import CampaignMetric


class CampaignTable:
    """Render a simple table of campaign metrics."""

    def __init__(self, metrics: Sequence[CampaignMetric]) -> None:
        self.metrics = metrics

    def show(self) -> None:
        import dearpygui.dearpygui as dpg

        with dpg.table(header_row=True):
            for name in ("Campaign", "Impressions", "Clicks", "Spend"):
                dpg.add_table_column(label=name)
            for metric in self.metrics:
                with dpg.table_row():
                    dpg.add_text(metric.campaign_id)
                    dpg.add_text(str(metric.impressions))
                    dpg.add_text(str(metric.clicks))
                    dpg.add_text(f"${metric.spend:,.2f}")