#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Line Chart Visualization Node
Creates interactive line charts for Atlas time series data
"""

import dearpygui.dearpygui as dpg
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))
from atlas_node_abc import AtlasNodeABC


class Node(AtlasNodeABC):
    """Line chart visualization node."""

    _ver = '0.0.1'

    node_label = 'Line Chart'
    node_tag = 'LineChart'

    def __init__(self):
        super().__init__()
        self._chart_width = 400
        self._chart_height = 300
        self._show_legend = True
        self._show_grid = True
        self._line_width = 2.0
        self._colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        self._chart_data = None

    def add_node(
        self,
        parent: str,
        node_id: int,
        pos: List[int] = [0, 0],
        atlas_config: Optional[Dict] = None,
        callback: Optional[callable] = None,
    ) -> str:
        """Create the visual representation of the line chart node."""
        # Tag names
        tag_node_name = str(node_id) + ':' + self.node_tag
        tag_node_input01_name = tag_node_name + ':' + self.TYPE_TIME_SERIES + ':Input01'
        tag_node_input01_value_name = tag_node_name + ':' + self.TYPE_TIME_SERIES + ':Input01Value'
        tag_node_input02_name = tag_node_name + ':' + self.TYPE_INT + ':Input02'
        tag_node_input02_value_name = tag_node_name + ':' + self.TYPE_INT + ':Input02Value'
        tag_node_input03_name = tag_node_name + ':' + self.TYPE_INT + ':Input03'
        tag_node_input03_value_name = tag_node_name + ':' + self.TYPE_INT + ':Input03Value'
        tag_node_output01_name = tag_node_name + ':' + self.TYPE_CHART + ':Output01'
        tag_node_output01_value_name = tag_node_name + ':' + self.TYPE_CHART + ':Output01Value'

        # Chart settings from config
        if atlas_config:
            chart_settings = atlas_config.get('chart_settings', {})
            self._chart_width = chart_settings.get('width', self._chart_width)
            self._chart_height = chart_settings.get('height', self._chart_height)

        # Node
        with dpg.node(
                tag=tag_node_name,
                parent=parent,
                label=self.node_label,
                pos=pos,
        ):
            # Time series input
            with dpg.node_attribute(
                    tag=tag_node_input01_name,
                    attribute_type=dpg.mvNode_Attr_Input,
            ):
                dpg.add_text(
                    tag=tag_node_input01_value_name,
                    default_value='Time Series Data',
                )

            # Chart width
            with dpg.node_attribute(
                    tag=tag_node_input02_name,
                    attribute_type=dpg.mvNode_Attr_Input,
            ):
                dpg.add_slider_int(
                    tag=tag_node_input02_value_name,
                    label="Width",
                    width=self._chart_width - 80,
                    default_value=self._chart_width,
                    min_value=200,
                    max_value=800,
                )

            # Chart height
            with dpg.node_attribute(
                    tag=tag_node_input03_name,
                    attribute_type=dpg.mvNode_Attr_Input,
            ):
                dpg.add_slider_int(
                    tag=tag_node_input03_value_name,
                    label="Height",
                    width=self._chart_width - 80,
                    default_value=self._chart_height,
                    min_value=150,
                    max_value=600,
                )

            # Chart display
            with dpg.node_attribute(
                    tag=tag_node_output01_name,
                    attribute_type=dpg.mvNode_Attr_Output,
            ):
                # Create plot for chart display
                with dpg.plot(
                    tag=f"{tag_node_name}_plot",
                    label="Time Series Chart",
                    width=self._chart_width,
                    height=self._chart_height,
                    anti_aliased=True,
                ):
                    dpg.add_plot_legend()
                    dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                    dpg.add_plot_axis(dpg.mvYAxis, label="Value", tag=f"{tag_node_name}_y_axis")

        return tag_node_name

    def update(
        self,
        node_id: int,
        connection_list: List[List[str]],
        node_data_dict: Dict[str, Any],
        node_result_dict: Dict[str, Any],
    ) -> tuple:
        """Process data and update chart visualization."""
        tag_node_name = str(node_id) + ':' + self.node_tag
        input_value02_tag = tag_node_name + ':' + self.TYPE_INT + ':Input02Value'
        input_value03_tag = tag_node_name + ':' + self.TYPE_INT + ':Input03Value'

        # Get chart dimensions
        try:
            chart_width = dpg.get_value(input_value02_tag)
            chart_height = dpg.get_value(input_value03_tag)
            self._chart_width = chart_width
            self._chart_height = chart_height
        except:
            pass

        # Get input data from connections
        input_data = None
        for connection_info in connection_list:
            connection_type = connection_info[0].split(':')[2]
            if connection_type == self.TYPE_TIME_SERIES:
                # Get source node name
                source_node_name = connection_info[0].split(':')[:2]
                source_node_name = ':'.join(source_node_name)
                input_data = node_data_dict.get(source_node_name, None)
                break

        if input_data:
            # Process time series data
            chart_data = self._process_time_series_data(input_data)
            if chart_data:
                self._update_chart_display(node_id, chart_data)
                return chart_data, {'chart_type': 'line', 'series_count': len(chart_data.get('series', []))}
            else:
                return None, {'error': 'Failed to process time series data'}
        else:
            return None, {'status': 'no_data'}

    def _process_time_series_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process Atlas time series data for chart display."""
        try:
            if 'time_series' not in data:
                return None

            chart_data = {
                'series': [],
                'time_range': data.get('metadata', {}),
                'chart_config': {
                    'width': self._chart_width,
                    'height': self._chart_height,
                    'show_legend': self._show_legend,
                    'show_grid': self._show_grid
                }
            }

            # Process each time series
            for i, ts in enumerate(data['time_series']):
                if 'data' in ts and 'values' in ts['data']:
                    values = ts['data']['values']
                    if not values:
                        continue

                    # Create time points
                    start_time = data.get('metadata', {}).get('start_time', 0)
                    step = data.get('metadata', {}).get('step', 60000)
                    timestamps = [start_time + j * step for j in range(len(values))]

                    # Convert to DearPyGui format
                    series_data = {
                        'label': ts.get('label', f'Series {i+1}'),
                        'x_values': timestamps,
                        'y_values': values,
                        'color': self._colors[i % len(self._colors)],
                        'line_width': self._line_width
                    }
                    chart_data['series'].append(series_data)

            return chart_data

        except Exception as e:
            print(f"Error processing time series data: {e}")
            return None

    def _update_chart_display(self, node_id: int, chart_data: Dict[str, Any]):
        """Update the chart display with new data."""
        tag_node_name = str(node_id) + ':' + self.node_tag
        plot_tag = f"{tag_node_name}_plot"
        y_axis_tag = f"{tag_node_name}_y_axis"

        try:
            # Clear existing series
            dpg.delete_item(plot_tag, children_only=True)

            # Recreate plot structure
            with dpg.plot(
                tag=plot_tag,
                label="Time Series Chart",
                width=self._chart_width,
                height=self._chart_height,
                anti_aliased=True,
                parent=dpg.last_item()
            ):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label="Time")
                dpg.add_plot_axis(dpg.mvYAxis, label="Value", tag=y_axis_tag)

                # Add data series
                for series in chart_data['series']:
                    dpg.add_line_series(
                        series['x_values'],
                        series['y_values'],
                        label=series['label'],
                        parent=y_axis_tag
                    )

        except Exception as e:
            print(f"Error updating chart display: {e}")

    def close(self, node_id: int) -> None:
        """Cleanup when node is deleted."""
        pass

    def get_setting_dict(self, node_id: int) -> Dict[str, Any]:
        """Return node configuration for saving."""
        tag_node_name = str(node_id) + ':' + self.node_tag
        input_value02_tag = tag_node_name + ':' + self.TYPE_INT + ':Input02Value'
        input_value03_tag = tag_node_name + ':' + self.TYPE_INT + ':Input03Value'

        try:
            chart_width = dpg.get_value(input_value02_tag)
            chart_height = dpg.get_value(input_value03_tag)
        except:
            chart_width = self._chart_width
            chart_height = self._chart_height

        pos = dpg.get_item_pos(tag_node_name)

        setting_dict = {
            'ver': self._ver,
            'pos': pos,
            'chart_width': chart_width,
            'chart_height': chart_height,
            'show_legend': self._show_legend,
            'show_grid': self._show_grid,
            'line_width': self._line_width
        }

        return setting_dict

    def set_setting_dict(self, node_id: int, setting_dict: Dict[str, Any]) -> None:
        """Restore node configuration from saved data."""
        tag_node_name = str(node_id) + ':' + self.node_tag
        input_value02_tag = tag_node_name + ':' + self.TYPE_INT + ':Input02Value'
        input_value03_tag = tag_node_name + ':' + self.TYPE_INT + ':Input03Value'

        chart_width = setting_dict.get('chart_width', self._chart_width)
        chart_height = setting_dict.get('chart_height', self._chart_height)
        self._show_legend = setting_dict.get('show_legend', self._show_legend)
        self._show_grid = setting_dict.get('show_grid', self._show_grid)
        self._line_width = setting_dict.get('line_width', self._line_width)

        dpg.set_value(input_value02_tag, chart_width)
        dpg.set_value(input_value03_tag, chart_height)

        self._chart_width = chart_width
        self._chart_height = chart_height
