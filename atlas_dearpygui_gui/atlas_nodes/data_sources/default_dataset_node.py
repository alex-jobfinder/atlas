"""
Default Dataset Node
Provides a pre-loaded sample dataset for immediate testing and demonstration
"""

import json
import os
import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))
from atlas_node_abc import AtlasNodeABC


class Node(AtlasNodeABC):
    """Default dataset node with pre-loaded sample data."""

    def __init__(self):
        super().__init__()
        self.node_tag = "default_dataset"
        self._dataset_loaded = False
        self._sample_data = None

    def add_node(self, parent: int, node_id: int, pos: list, size: list = [200, 150]) -> int:
        """Create the default dataset node."""
        with dpg.node(
            parent=parent,
            tag=node_id,
            label="Default Dataset",
            pos=pos,
            size=size
        ):
            # Output port for time series data
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, tag=str(node_id) + ':' + self.TYPE_TIME_SERIES + ':Output01Value'):
                dpg.add_text("Time Series Data")

            # Load dataset button
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(
                    label="Load Sample Data",
                    callback=self._load_sample_data,
                    user_data=node_id,
                    width=size[0] - 20
                )

            # Status display
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                self._status_text = dpg.add_text("Click to load sample data", wrap=size[0] - 20)

        return node_id

    def _load_sample_data(self, sender, app_data, user_data):
        """Load the sample dataset."""
        node_id = user_data

        try:
            # Load default dataset
            data_file = Path(__file__).parent.parent.parent / 'data' / 'default_dataset.json'
            if data_file.exists():
                with data_file.open('r') as f:
                    self._sample_data = json.load(f)

                self._dataset_loaded = True

                # Update status
                dpg.set_value(self._status_text, f"Loaded: {len(self._sample_data.get('plots', []))} plots")

                print(f"Default dataset loaded successfully from {data_file}")
            else:
                dpg.set_value(self._status_text, "Error: Default dataset not found")
                print(f"Default dataset file not found: {data_file}")

        except Exception as e:
            dpg.set_value(self._status_text, f"Error loading dataset: {str(e)}")
            print(f"Error loading default dataset: {e}")

    def update(self, node_id: int, node_data_dict: Dict, node_result_dict: Dict) -> None:
        """Update the node with sample data."""
        if not self._dataset_loaded or not self._sample_data:
            return

        # Create time series data from the sample dataset
        time_series_data = []

        for plot in self._sample_data.get('plots', []):
            for line in plot.get('lines', []):
                line_data = line.get('data', {})
                if 'data' in line_data:
                    ts_data = line_data['data']
                    time_series_data.append({
                        'tags': line_data.get('tags', {}),
                        'label': line_data.get('label', 'Unknown'),
                        'start_time': ts_data.get('startTime'),
                        'step': ts_data.get('step', 60000),
                        'values': ts_data.get('values', []),
                        'color': line.get('color', '#1f77b4'),
                        'line_width': line.get('lineWidth', 2)
                    })

        # Store the processed data
        node_data_dict[node_id] = {
            'time_series': time_series_data,
            'metadata': {
                'title': self._sample_data.get('title', 'Default Dataset'),
                'start_time': self._sample_data.get('startTime'),
                'end_time': self._sample_data.get('endTime'),
                'step': self._sample_data.get('step', 60000),
                'source': 'default_dataset'
            }
        }

        node_result_dict[node_id] = {
            'status': 'success',
            'message': f'Loaded {len(time_series_data)} time series',
            'data_points': sum(len(ts['values']) for ts in time_series_data)
        }

    def get_setting_dict(self, node_id: int) -> Dict:
        """Get node settings for saving."""
        return {
            'dataset_loaded': self._dataset_loaded,
            'node_type': 'default_dataset'
        }

    def set_setting_dict(self, node_id: int, setting: Dict) -> None:
        """Restore node settings from saved data."""
        self._dataset_loaded = setting.get('dataset_loaded', False)

        # If dataset was loaded, reload it
        if self._dataset_loaded:
            self._load_sample_data(None, None, node_id)

    def close(self, node_id: int) -> None:
        """Cleanup when node is deleted."""
        self._dataset_loaded = False
        self._sample_data = None
