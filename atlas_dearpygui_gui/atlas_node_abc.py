#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Atlas Node Abstract Base Class
Adapted from Image-Processing-Node-Editor architecture for time series data visualization
"""

from abc import ABCMeta, abstractmethod
from typing import Dict, List, Optional, Any, Union
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json


class AtlasNodeABC(metaclass=ABCMeta):
    """
    Abstract base class for all Atlas visualization nodes.
    Adapted from DpgNodeABC for time series data processing.
    """

    _ver = '0.0.0'

    node_label = ''
    node_tag = ''

    # Atlas-specific data types
    TYPE_TIME_SERIES = 'TimeSeries'
    TYPE_DATAFRAME = 'DataFrame'
    TYPE_CHART = 'Chart'
    TYPE_QUERY = 'Query'
    TYPE_METADATA = 'Metadata'
    TYPE_TIME_RANGE = 'TimeRange'
    TYPE_ALERT_RULE = 'AlertRule'

    # Legacy types for compatibility
    TYPE_INT = 'Int'
    TYPE_FLOAT = 'Float'
    TYPE_TEXT = 'Text'
    TYPE_TIME_MS = 'TimeMS'

    def __init__(self):
        """Initialize the node with default settings."""
        self._atlas_config = None
        self._time_range = None
        self._theme = 'light'

    @abstractmethod
    def add_node(
        self,
        parent: str,
        node_id: int,
        pos: List[int] = [0, 0],
        atlas_config: Optional[Dict] = None,
        callback: Optional[callable] = None,
    ) -> str:
        """
        Create the visual representation of the node in the editor.

        Args:
            parent: Parent node editor tag
            node_id: Unique node identifier
            pos: Position [x, y] for node placement
            atlas_config: Atlas-specific configuration
            callback: Optional callback function

        Returns:
            Node tag name for identification
        """
        pass

    @abstractmethod
    def update(
        self,
        node_id: int,
        connection_list: List[List[str]],
        node_data_dict: Dict[str, Any],
        node_result_dict: Dict[str, Any],
    ) -> tuple:
        """
        Process data and update node outputs.

        Args:
            node_id: Node identifier
            connection_list: List of input connections
            node_data_dict: Shared data dictionary for time series data
            node_result_dict: Shared result dictionary for metadata

        Returns:
            Tuple of (processed_data, metadata)
        """
        pass

    @abstractmethod
    def get_setting_dict(self, node_id: int) -> Dict[str, Any]:
        """
        Return node configuration for saving.

        Args:
            node_id: Node identifier

        Returns:
            Dictionary containing node settings
        """
        pass

    @abstractmethod
    def set_setting_dict(self, node_id: int, setting_dict: Dict[str, Any]) -> None:
        """
        Restore node configuration from saved data.

        Args:
            node_id: Node identifier
            setting_dict: Dictionary containing saved settings
        """
        pass

    @abstractmethod
    def close(self, node_id: int) -> None:
        """
        Cleanup when node is deleted.

        Args:
            node_id: Node identifier
        """
        pass

    def validate_time_series_data(self, data: Any) -> bool:
        """
        Validate that data is a proper time series format.

        Args:
            data: Data to validate

        Returns:
            True if valid time series data
        """
        if isinstance(data, pd.DataFrame):
            return 'timestamp' in data.columns or isinstance(data.index, pd.DatetimeIndex)
        elif isinstance(data, pd.Series):
            return isinstance(data.index, pd.DatetimeIndex)
        elif isinstance(data, dict) and 'data' in data and 'tags' in data:
            return True
        return False

    def apply_atlas_styling(self, chart_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply Atlas-specific styling to chart configuration.

        Args:
            chart_config: Base chart configuration

        Returns:
            Styled chart configuration
        """
        atlas_theme = {
            'light': {
                'background_color': '#FFFFFF',
                'grid_color': '#E0E0E0',
                'text_color': '#000000',
                'line_colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            },
            'dark': {
                'background_color': '#1E1E1E',
                'grid_color': '#404040',
                'text_color': '#FFFFFF',
                'line_colors': ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
            }
        }

        theme_config = atlas_theme.get(self._theme, atlas_theme['light'])
        chart_config.update(theme_config)
        return chart_config

    def handle_time_range_updates(self, time_range: Dict[str, Any]) -> None:
        """
        Handle time range updates from the editor.

        Args:
            time_range: Dictionary with start_time, end_time, step
        """
        self._time_range = time_range

    def process_query_results(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Atlas query results into standardized format.

        Args:
            query_result: Raw query result from Atlas API

        Returns:
            Processed time series data
        """
        if 'data' not in query_result:
            return {'error': 'Invalid query result format'}

        processed_data = {
            'time_series': [],
            'metadata': {
                'query': query_result.get('query', ''),
                'start_time': query_result.get('start', 0),
                'end_time': query_result.get('end', 0),
                'step': query_result.get('step', 60000)
            }
        }

        # Process each time series in the result
        for series_data in query_result['data']:
            ts_data = {
                'tags': series_data.get('tags', {}),
                'label': series_data.get('label', ''),
                'data': series_data.get('data', []),
                'query': series_data.get('query', ''),
                'groupByKeys': series_data.get('groupByKeys', [])
            }
            processed_data['time_series'].append(ts_data)

        return processed_data

    def convert_to_dataframe(self, time_series_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Convert Atlas time series data to pandas DataFrame.

        Args:
            time_series_data: Atlas time series data

        Returns:
            pandas DataFrame with timestamp index
        """
        if 'time_series' not in time_series_data:
            return pd.DataFrame()

        dfs = []
        for ts in time_series_data['time_series']:
            if 'data' in ts and 'values' in ts['data']:
                values = ts['data']['values']
                start_time = time_series_data['metadata']['start_time']
                step = time_series_data['metadata']['step']

                # Create timestamp index
                timestamps = [start_time + i * step for i in range(len(values))]
                df = pd.DataFrame({
                    'timestamp': timestamps,
                    'value': values,
                    'label': ts.get('label', ''),
                    'tags': json.dumps(ts.get('tags', {}))
                })
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                df.set_index('timestamp', inplace=True)
                dfs.append(df)

        if dfs:
            return pd.concat(dfs, ignore_index=False)
        return pd.DataFrame()

    def get_node_tag(self, node_id: int) -> str:
        """Get the tag name for this node."""
        return f"{node_id}:{self.node_tag}"

    def get_input_tag(self, node_id: int, input_name: str, data_type: str) -> str:
        """Get the tag name for an input port."""
        return f"{node_id}:{self.node_tag}:{data_type}:{input_name}"

    def get_output_tag(self, node_id: int, output_name: str, data_type: str) -> str:
        """Get the tag name for an output port."""
        return f"{node_id}:{self.node_tag}:{data_type}:{output_name}"
