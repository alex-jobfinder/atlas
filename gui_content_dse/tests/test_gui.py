import os
import unittest
from pathlib import Path

import dearpygui.dearpygui as dpg

from gui_content_dse.main import ContentDSEApp


class TestCampaignPerformanceGUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Build a small sample CSV in the workspace
        cls.tmp_dir = Path("gui_content_dse/tests/tmp")
        cls.tmp_dir.mkdir(parents=True, exist_ok=True)
        cls.csv_path = cls.tmp_dir / "sample_campaign.csv"
        cls.csv_path.write_text(
            """time,impressions,clicks,spend\n"""
            "2025-01-01,1000,50,12.5\n"
            "2025-01-02,2000,80,20.0\n"
            "2025-01-03,1500,60,15.0\n",
            encoding="utf-8",
        )

    @classmethod
    def tearDownClass(cls):
        # Clean up temp files
        try:
            if cls.csv_path.exists():
                cls.csv_path.unlink()
            # Do not remove directory in case of other artifacts
        except Exception:
            pass

    def setUp(self):
        self.app = ContentDSEApp()
        # Headless init to avoid OS window requirements
        self.app.init(show_viewport=False)

    def tearDown(self):
        self.app.shutdown()

    def test_tab_and_sidebar_exist(self):
        # Verify the core items are created
        self.assertTrue(dpg.does_item_exist("campaign_performance_tab"))
        self.assertIsNotNone(self.app._sidebar)
        self.assertTrue(dpg.does_item_exist(self.app._sidebar))
        self.assertIsNotNone(self.app._plot)
        self.assertTrue(dpg.does_item_exist(self.app._plot))

    def test_load_csv_populates_metrics_and_renders_series(self):
        # Set paths and load
        dpg.set_value(self.app._csv_input, str(self.csv_path))
        # no YAML for this test
        dpg.set_value(self.app._yaml_input, "")
        self.app._load_and_render()

        # Metrics detected (impressions, clicks, spend)
        cfg = dpg.get_item_configuration(self.app._metric_combo)
        items = cfg.get("items", [])
        self.assertTrue(any("impressions" in it for it in items))
        self.assertTrue(any("clicks" in it for it in items))
        self.assertTrue(any("spend" in it for it in items))

        # A default metric is selected and a line series is created
        self.assertIsNotNone(self.app._series_tag)
        self.assertTrue(dpg.does_item_exist(self.app._series_tag))
        # Series should be a child of y-axis
        children = dpg.get_item_children(self.app._y_axis, slot=1)
        self.assertIn(self.app._series_tag, children)

    def test_switch_metric_re_renders(self):
        dpg.set_value(self.app._csv_input, str(self.csv_path))
        self.app._load_and_render()
        # Find a metric with a distinct name
        cfg = dpg.get_item_configuration(self.app._metric_combo)
        items = cfg.get("items", [])
        # Choose clicks if available
        target_disp = next((i for i in items if i.startswith("clicks")), items[0])
        # Trigger metric change
        self.app._on_metric_change(target_disp)
        # Confirm series exists and label matches metric
        self.assertTrue(dpg.does_item_exist(self.app._series_tag))
        # Nothing else to assert about data values without accessing DearPyGui internals


if __name__ == "__main__":
    unittest.main(verbosity=2)

