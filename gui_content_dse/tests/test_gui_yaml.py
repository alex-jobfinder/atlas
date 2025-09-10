import unittest
from pathlib import Path

import dearpygui.dearpygui as dpg

from gui_content_dse.main import ContentDSEApp


class TestCampaignPerformanceYAMLSemantics(unittest.TestCase):
    def setUp(self):
        self.app = ContentDSEApp()
        self.app.init(show_viewport=False)

    def tearDown(self):
        self.app.shutdown()

    def test_yaml_semantics_and_campaign_filter(self):
        csv_path = Path("gui_content_dse/data/slim/campaign_performance_slim.csv")
        yaml_path = Path("gui_content_dse/data/slim/campaign_performance_slim.yml")
        self.assertTrue(csv_path.exists())
        self.assertTrue(yaml_path.exists())

        # Load
        dpg.set_value(self.app._csv_input, str(csv_path))
        dpg.set_value(self.app._yaml_input, str(yaml_path))
        self.app._load_and_render()

        # Metric items include key YAML measures
        items = dpg.get_item_configuration(self.app._metric_combo).get("items", [])
        self.assertTrue(any(i.startswith("impressions") for i in items))
        self.assertTrue(any(i.startswith("clicks") for i in items))
        self.assertTrue(any(i.startswith("spend") for i in items))

        # Campaign combo includes All + at least one campaign id
        campaigns = dpg.get_item_configuration(self.app._campaign_combo).get("items", [])
        self.assertIn("All", campaigns)
        self.assertTrue(any(c != "All" for c in campaigns))

        # Selecting a specific campaign renders a series
        specific = next((c for c in campaigns if c != "All"), None)
        self.assertIsNotNone(specific)
        dpg.set_value(self.app._campaign_combo, specific)
        self.app._render_series()
        self.assertIsNotNone(self.app._series_tag)
        self.assertTrue(dpg.does_item_exist(self.app._series_tag))


if __name__ == "__main__":
    unittest.main(verbosity=2)

