"""Default Dataset Node
Provides a pre-loaded sample dataset for immediate testing and demonstration."""

import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional, Any

from atlas_dearpygui_gui.atlas_node_abc import AtlasNodeABC
from atlas_dearpygui_gui.utils.default_dataset_loader import (
    load_default_dataset,
    format_dataset,
)


class Node(AtlasNodeABC):
    """Default dataset node with pre-loaded sample data."""

    node_label = "Default Dataset"
    node_tag = "DefaultDataset"

    def __init__(self):
        super().__init__()
        self._dataset_loaded = False
        self._sample_data: Optional[Dict[str, Any]] = None
        self._status_text = None

    def add_node(
        self,
        parent: str,
        node_id: int,
        pos: List[int],
        atlas_config: Optional[Dict] = None,
        callback: Optional[callable] = None,
        size: List[int] = [200, 150],
    ) -> str:
        """Create the default dataset node."""

        tag_node_name = f"{node_id}:{self.node_tag}"
        tag_output01 = f"{tag_node_name}:{self.TYPE_TIME_SERIES}:Output01"
        tag_output01_value = f"{tag_node_name}:{self.TYPE_TIME_SERIES}:Output01Value"

        # Check auto load option
        self._auto_load = False
        if atlas_config:
            default_cfg = atlas_config.get("default_dataset", {})
            self._auto_load = default_cfg.get("auto_load", False)

        with dpg.node(
            parent=parent,
            tag=tag_node_name,
            label=self.node_label,
            pos=pos,
        ):
            # Output port for time series data
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output,
                tag=tag_output01,
            ):
                dpg.add_text(tag=tag_output01_value, default_value="Time Series Data")

            # Load dataset button
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(
                    label="Load Sample Data",
                    callback=self._load_sample_data,
                    user_data=node_id,
                    width=size[0] - 20,
                )

            # Status display
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                self._status_text = dpg.add_text(
                    "Click to load sample data", wrap=size[0] - 20
                )

        if self._auto_load:
            self._load_sample_data(None, None, node_id)

        return tag_node_name

    def _load_sample_data(self, sender, app_data, user_data):
        """Load the sample dataset using the shared loader."""
        try:
            self._sample_data = load_default_dataset()
            self._dataset_loaded = True
            dpg.set_value(
                self._status_text,
                f"Loaded: {len(self._sample_data.get('plots', []))} plots",
            )
        except Exception as e:
            dpg.set_value(self._status_text, f"Error loading dataset: {e}")

    def update(
        self,
        node_id: int,
        connection_list: List[List[str]],
        node_data_dict: Dict[str, Any],
        node_result_dict: Dict[str, Any],
    ) -> tuple:
        """Update the node with sample data."""
        if not self._dataset_loaded or not self._sample_data:
            return None, {"status": "no_data"}

        data = format_dataset(self._sample_data)
        time_series = data.get("time_series", [])
        result = {
            "status": "success",
            "message": f"Loaded {len(time_series)} time series",
            "data_points": sum(len(ts["data"]["values"]) for ts in time_series),
        }
        return data, result

    def get_setting_dict(self, node_id: int) -> Dict:
        """Get node settings for saving."""
        return {
            "dataset_loaded": self._dataset_loaded,
            "node_type": "default_dataset",
        }

    def set_setting_dict(self, node_id: int, setting: Dict) -> None:
        """Restore node settings from saved data."""
        self._dataset_loaded = setting.get("dataset_loaded", False)
        if self._dataset_loaded:
            self._load_sample_data(None, None, node_id)

    def close(self, node_id: int) -> None:
        """Cleanup when node is deleted."""
        self._dataset_loaded = False
        self._sample_data = None
