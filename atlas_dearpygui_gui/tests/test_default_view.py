import unittest
from collections import OrderedDict
from pathlib import Path

import dearpygui.dearpygui as dpg

from atlas_dearpygui_gui.main import (
    load_atlas_config,
    initialize_default_view,
    update_node_info,
)
from atlas_dearpygui_gui.atlas_node_editor import AtlasNodeEditor


class TestDefaultView(unittest.TestCase):
    def setUp(self):
        dpg.create_context()
        dpg.create_viewport(width=600, height=400)
        dpg.setup_dearpygui()

    def tearDown(self):
        if dpg.is_viewport_created():
            dpg.destroy_viewport()
        # destroy_context triggers a segfault with Dear PyGui 2.x in headless mode
        # so we rely on interpreter cleanup after tests

    def _create_editor(self, config):
        base_dir = Path(__file__).resolve().parents[1]
        menu = OrderedDict({
            "Data Sources": "data_sources",
            "Visualization": "visualization",
        })
        return AtlasNodeEditor(
            width=600,
            height=400,
            atlas_config=config,
            menu_dict=menu,
            node_dir=str(base_dir / "atlas_nodes"),
        )

    def test_default_dataset_autoloads_and_renders(self):
        base_dir = Path(__file__).resolve().parents[1]
        config_path = base_dir / "config" / "atlas_config.json"
        config = load_atlas_config(str(config_path))
        config.setdefault("default_dataset", {})
        config["default_dataset"].update({"enabled": True, "auto_load": True})

        editor = self._create_editor(config)
        initialize_default_view(editor, config)

        dataset_instance = editor.get_node_instance("DefaultDataset")
        self.assertTrue(dataset_instance._dataset_loaded)
        self.assertIsNotNone(dataset_instance._sample_data)

        node_data = {}
        node_results = {}
        update_node_info(editor, node_data, node_results, mode_async=False)

        chart_tag = next(n for n in editor.get_node_list() if n.endswith(":LineChart"))
        chart_data = node_data.get(chart_tag)
        self.assertIsNotNone(chart_data)
        self.assertGreater(len(chart_data.get("series", [])), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
