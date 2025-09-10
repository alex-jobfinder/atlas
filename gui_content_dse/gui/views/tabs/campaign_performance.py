from __future__ import annotations

import dearpygui.dearpygui as dpg
from gui_content_dse.gui.controllers.campaign_performance import CampaignPerformanceController


class CampaignPerformanceView:
    def __init__(self, controller: CampaignPerformanceController):
        self.controller = controller

    def build(self):
        self.controller.build_ui()

