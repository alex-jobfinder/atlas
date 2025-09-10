#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
JSON Import Node
Imports Atlas GraphDef JSON files (V1 and V2 formats)
"""

import json
import gzip
import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))
from atlas_node_abc import AtlasNodeABC


class Node(AtlasNodeABC):
    """JSON import node for Atlas GraphDef files."""

    _ver = '0.0.1'

    node_label = 'JSON Import'
    node_tag = 'JSONImport'

    def __init__(self):
        super().__init__()
        self._file_path = ""
        self._format_version = "auto"
        self._loaded_data = None

    def add_node(
        self,
        parent: str,
        node_id: int,
        pos: List[int] = [0, 0],
        atlas_config: Optional[Dict] = None,
        callback: Optional[callable] = None,
    ) -> str:
        """Create the visual representation of the JSON import node."""
        # Tag names
        tag_node_name = str(node_id) + ':' + self.node_tag
        tag_node_input01_name = tag_node_name + ':' + self.TYPE_TEXT + ':Input01'
        tag_node_input01_value_name = tag_node_name + ':' + self.TYPE_TEXT + ':Input01Value'
        tag_node_output01_name = tag_node_name + ':' + self.TYPE_TIME_SERIES + ':Output01'
        tag_node_output01_value_name = tag_node_name + ':' + self.TYPE_TIME_SERIES + ':Output01Value'
        tag_node_output02_name = tag_node_name + ':' + self.TYPE_CHART + ':Output02'
        tag_node_output02_value_name = tag_node_name + ':' + self.TYPE_CHART + ':Output02Value'
        tag_node_output03_name = tag_node_name + ':' + self.TYPE_METADATA + ':Output03'
        tag_node_output03_value_name = tag_node_name + ':' + self.TYPE_METADATA + ':Output03Value'

        # File dialog for JSON selection
        with dpg.file_dialog(
                directory_selector=False,
                show=False,
                modal=True,
                height=400,
                callback=self._callback_file_select,
                id=f'json_select:{node_id}',
        ):
            dpg.add_file_extension(
                'JSON Files (*.json *.json.gz){.json,.json.gz}')
            dpg.add_file_extension('', color=(150, 255, 150, 255))

        # Node
        with dpg.node(
                tag=tag_node_name,
                parent=parent,
                label=self.node_label,
                pos=pos,
        ):
            # File selection
            with dpg.node_attribute(
                    tag=tag_node_input01_name,
                    attribute_type=dpg.mvNode_Attr_Static,
            ):
                dpg.add_button(
                    label='Select JSON File',
                    width=200,
                    callback=lambda: dpg.show_item(f'json_select:{node_id}'),
                )
                dpg.add_text(
                    tag=tag_node_input01_value_name,
                    default_value="No file selected",
                )

            # Format selection
            with dpg.node_attribute(
                    attribute_type=dpg.mvNode_Attr_Static,
            ):
                dpg.add_combo(
                    items=["auto", "v1", "v2"],
                    default_value="auto",
                    label="Format",
                    width=100,
                    callback=lambda s, a, u: self._set_format_version(a),
                )

            # Time series output
            with dpg.node_attribute(
                    tag=tag_node_output01_name,
                    attribute_type=dpg.mvNode_Attr_Output,
            ):
                dpg.add_text(
                    tag=tag_node_output01_value_name,
                    default_value="Time Series Data",
                )

            # Chart definition output
            with dpg.node_attribute(
                    tag=tag_node_output02_name,
                    attribute_type=dpg.mvNode_Attr_Output,
            ):
                dpg.add_text(
                    tag=tag_node_output02_value_name,
                    default_value="Chart Definition",
                )

            # Metadata output
            with dpg.node_attribute(
                    tag=tag_node_output03_name,
                    attribute_type=dpg.mvNode_Attr_Output,
            ):
                dpg.add_text(
                    tag=tag_node_output03_value_name,
                    default_value="File Metadata",
                )

        return tag_node_name

    def update(
        self,
        node_id: int,
        connection_list: List[List[str]],
        node_data_dict: Dict[str, Any],
        node_result_dict: Dict[str, Any],
    ) -> tuple:
        """Process data and update node outputs."""
        tag_node_name = str(node_id) + ':' + self.node_tag
        output_value01_tag = tag_node_name + ':' + self.TYPE_TIME_SERIES + ':Output01Value'
        output_value02_tag = tag_node_name + ':' + self.TYPE_CHART + ':Output02Value'
        output_value03_tag = tag_node_name + ':' + self.TYPE_METADATA + ':Output03Value'

        if self._loaded_data:
            # Update output displays
            time_series_count = len(self._loaded_data.get('time_series', []))
            dpg.set_value(output_value01_tag, f"Loaded {time_series_count} time series")

            chart_info = self._loaded_data.get('chart_definition', {})
            plot_count = len(chart_info.get('plots', []))
            dpg.set_value(output_value02_tag, f"Chart with {plot_count} plots")

            metadata = self._loaded_data.get('metadata', {})
            file_info = f"Format: {metadata.get('format', 'unknown')}"
            dpg.set_value(output_value03_tag, file_info)

            return self._loaded_data, metadata
        else:
            dpg.set_value(output_value01_tag, "No data loaded")
            dpg.set_value(output_value02_tag, "No chart definition")
            dpg.set_value(output_value03_tag, "No file selected")
            return None, {'status': 'no_data'}

    def _callback_file_select(self, sender, data):
        """Callback for file selection."""
        if data['file_name'] != '.':
            node_id = sender.split(':')[1]
            file_path = data['file_path_name']
            self._file_path = file_path

            # Update display
            tag_node_name = f"{node_id}:{self.node_tag}"
            input_value01_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input01Value'
            dpg.set_value(input_value01_tag, Path(file_path).name)

            # Load the file
            self._load_json_file(file_path)

    def _set_format_version(self, version: str):
        """Set the format version."""
        self._format_version = version
        if self._file_path:
            self._load_json_file(self._file_path)

    def _load_json_file(self, file_path: str):
        """Load JSON file and parse Atlas data."""
        try:
            # Determine if file is gzipped
            if file_path.lower().endswith('.gz'):
                with gzip.open(file_path, 'rt') as f:
                    data = json.load(f)
            else:
                with open(file_path, 'r') as f:
                    data = json.load(f)

            # Determine format if auto
            format_version = self._format_version
            if format_version == "auto":
                if file_path.lower().endswith('.gz'):
                    format_version = "v2"
                elif 'plots' in data and 'startTime' in data:
                    format_version = "v2"
                else:
                    format_version = "v1"

            # Parse based on format
            if format_version == "v2":
                parsed_data = self._parse_v2_format(data)
            else:
                parsed_data = self._parse_v1_format(data)

            self._loaded_data = parsed_data
            print(f"Successfully loaded {format_version} JSON file: {os.path.basename(file_path)}")

        except Exception as e:
            print(f"Failed to load JSON file {file_path}: {e}")
            self._loaded_data = None

    def _parse_v2_format(self, data: Dict) -> Dict:
        """Parse V2 JsonCodec format."""
        parsed_data = {
            'time_series': [],
            'chart_definition': data,
            'metadata': {
                'format': 'v2',
                'file_path': self._file_path
            }
        }

        # Extract time series from plots
        plots = data.get('plots', [])
        for plot in plots:
            for line_def in plot.get('data', []):
                if 'data' in line_def:
                    ts_data = {
                        'tags': line_def.get('tags', {}),
                        'label': line_def.get('label', ''),
                        'data': line_def.get('data', {}),
                        'query': line_def.get('query', ''),
                        'groupByKeys': line_def.get('groupByKeys', []),
                        'color': line_def.get('color', '#FF0000'),
                        'lineStyle': line_def.get('lineStyle', 'LINE')
                    }
                    parsed_data['time_series'].append(ts_data)

        return parsed_data

    def _parse_v1_format(self, data: Dict) -> Dict:
        """Parse V1 API format."""
        parsed_data = {
            'time_series': [],
            'chart_definition': {
                'plots': [],
                'startTime': data.get('start', 0),
                'endTime': data.get('start', 0) + data.get('step', 60000) * len(data.get('values', [[]])[0]),
                'step': data.get('step', 60000)
            },
            'metadata': {
                'format': 'v1',
                'file_path': self._file_path
            }
        }

        # Convert V1 format to time series
        start_time = data.get('start', 0)
        step = data.get('step', 60000)
        values = data.get('values', [])
        metrics = data.get('metrics', [])
        legend = data.get('legend', [])

        for i, (metric, legend_text) in enumerate(zip(metrics, legend)):
            if i < len(values):
                ts_data = {
                    'tags': metric,
                    'label': legend_text,
                    'data': {
                        'values': values[i]
                    },
                    'query': '',
                    'groupByKeys': [],
                    'color': '#FF0000',
                    'lineStyle': 'LINE'
                }
                parsed_data['time_series'].append(ts_data)

        return parsed_data

    def close(self, node_id: int) -> None:
        """Cleanup when node is deleted."""
        pass

    def get_setting_dict(self, node_id: int) -> Dict[str, Any]:
        """Return node configuration for saving."""
        tag_node_name = str(node_id) + ':' + self.node_tag

        pos = dpg.get_item_pos(tag_node_name)

        setting_dict = {
            'ver': self._ver,
            'pos': pos,
            'file_path': self._file_path,
            'format_version': self._format_version
        }

        return setting_dict

    def set_setting_dict(self, node_id: int, setting_dict: Dict[str, Any]) -> None:
        """Restore node configuration from saved data."""
        self._file_path = setting_dict.get('file_path', '')
        self._format_version = setting_dict.get('format_version', 'auto')

        # Update display
        tag_node_name = str(node_id) + ':' + self.node_tag
        input_value01_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input01Value'

        if self._file_path:
            dpg.set_value(input_value01_tag, Path(self._file_path).name)
            self._load_json_file(self._file_path)
        else:
            dpg.set_value(input_value01_tag, "No file selected")
