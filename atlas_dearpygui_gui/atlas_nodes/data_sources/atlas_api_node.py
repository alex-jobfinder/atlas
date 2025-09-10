#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Atlas API Data Source Node
Connects to Atlas API and executes queries to fetch time series data
"""

import requests
import json
import dearpygui.dearpygui as dpg
from typing import Dict, List, Optional, Any
import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))
from atlas_node_abc import AtlasNodeABC


class Node(AtlasNodeABC):
    """Atlas API data source node."""

    _ver = '0.0.1'

    node_label = 'Atlas API'
    node_tag = 'AtlasAPI'

    def __init__(self):
        super().__init__()
        self._api_endpoint = "http://localhost:7101"
        self._query_string = ""
        self._time_range = {
            'start': 'e-1h',
            'end': 'now',
            'step': '60s'
        }
        self._auth_token = None
        self._session = requests.Session()

    def add_node(
        self,
        parent: str,
        node_id: int,
        pos: List[int] = [0, 0],
        atlas_config: Optional[Dict] = None,
        callback: Optional[callable] = None,
    ) -> str:
        """Create the visual representation of the Atlas API node."""
        # Tag names
        tag_node_name = str(node_id) + ':' + self.node_tag
        tag_node_input01_name = tag_node_name + ':' + self.TYPE_TEXT + ':Input01'
        tag_node_input01_value_name = tag_node_name + ':' + self.TYPE_TEXT + ':Input01Value'
        tag_node_input02_name = tag_node_name + ':' + self.TYPE_TEXT + ':Input02'
        tag_node_input02_value_name = tag_node_name + ':' + self.TYPE_TEXT + ':Input02Value'
        tag_node_input03_name = tag_node_name + ':' + self.TYPE_TEXT + ':Input03'
        tag_node_input03_value_name = tag_node_name + ':' + self.TYPE_TEXT + ':Input03Value'
        tag_node_output01_name = tag_node_name + ':' + self.TYPE_TIME_SERIES + ':Output01'
        tag_node_output01_value_name = tag_node_name + ':' + self.TYPE_TIME_SERIES + ':Output01Value'
        tag_node_output02_name = tag_node_name + ':' + self.TYPE_METADATA + ':Output02'
        tag_node_output02_value_name = tag_node_name + ':' + self.TYPE_METADATA + ':Output02Value'

        # Atlas configuration
        if atlas_config:
            self._api_endpoint = atlas_config.get('api_endpoint', self._api_endpoint)
            self._auth_token = atlas_config.get('auth_token', self._auth_token)

        # Node
        with dpg.node(
                tag=tag_node_name,
                parent=parent,
                label=self.node_label,
                pos=pos,
        ):
            # Query input
            with dpg.node_attribute(
                    tag=tag_node_input01_name,
                    attribute_type=dpg.mvNode_Attr_Input,
            ):
                dpg.add_input_text(
                    tag=tag_node_input01_value_name,
                    label="Query",
                    width=200,
                    default_value=self._query_string,
                    hint="Atlas Query Language (AQL)",
                )

            # Time range input
            with dpg.node_attribute(
                    tag=tag_node_input02_name,
                    attribute_type=dpg.mvNode_Attr_Input,
            ):
                dpg.add_input_text(
                    tag=tag_node_input02_value_name,
                    label="Start",
                    width=100,
                    default_value=self._time_range['start'],
                    hint="e.g., e-1h, 2023-01-01T00:00:00Z",
                )
                dpg.add_input_text(
                    tag=tag_node_input02_value_name + "_end",
                    label="End",
                    width=100,
                    default_value=self._time_range['end'],
                    hint="e.g., now, 2023-01-01T01:00:00Z",
                )

            # API endpoint input
            with dpg.node_attribute(
                    tag=tag_node_input03_name,
                    attribute_type=dpg.mvNode_Attr_Input,
            ):
                dpg.add_input_text(
                    tag=tag_node_input03_value_name,
                    label="API Endpoint",
                    width=200,
                    default_value=self._api_endpoint,
                    hint="Atlas API endpoint URL",
                )

            # Execute button
            with dpg.node_attribute(
                    attribute_type=dpg.mvNode_Attr_Static,
            ):
                dpg.add_button(
                    label="Execute Query",
                    width=200,
                    callback=lambda: self._execute_query(node_id),
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

            # Metadata output
            with dpg.node_attribute(
                    tag=tag_node_output02_name,
                    attribute_type=dpg.mvNode_Attr_Output,
            ):
                dpg.add_text(
                    tag=tag_node_output02_value_name,
                    default_value="Query Metadata",
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
        output_value02_tag = tag_node_name + ':' + self.TYPE_METADATA + ':Output02Value'

        # Get current query parameters
        input_value01_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input01Value'
        input_value02_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input02Value'
        input_value03_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input03Value'

        try:
            query = dpg.get_value(input_value01_tag)
            start_time = dpg.get_value(input_value02_tag)
            end_time = dpg.get_value(input_value02_tag + "_end")
            api_endpoint = dpg.get_value(input_value03_tag)

            # Update internal state
            self._query_string = query
            self._time_range = {'start': start_time, 'end': end_time}
            self._api_endpoint = api_endpoint

            # Execute query if we have a valid query string
            if query and query.strip():
                result = self._execute_atlas_query(query, start_time, end_time, api_endpoint)

                if result and 'data' in result:
                    # Update output displays
                    dpg.set_value(output_value01_tag, f"Loaded {len(result['data'])} time series")
                    dpg.set_value(output_value02_tag, f"Query: {query[:50]}...")

                    return result, {'query': query, 'endpoint': api_endpoint}
                else:
                    dpg.set_value(output_value01_tag, "No data returned")
                    dpg.set_value(output_value02_tag, "Query failed")
                    return None, {'error': 'Query failed'}
            else:
                dpg.set_value(output_value01_tag, "Enter query to execute")
                dpg.set_value(output_value02_tag, "Ready")
                return None, {'status': 'ready'}

        except Exception as e:
            dpg.set_value(output_value01_tag, f"Error: {str(e)}")
            dpg.set_value(output_value02_tag, "Query failed")
            return None, {'error': str(e)}

    def _execute_query(self, node_id: int):
        """Execute the Atlas query manually."""
        tag_node_name = str(node_id) + ':' + self.node_tag
        input_value01_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input01Value'
        input_value02_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input02Value'
        input_value03_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input03Value'

        query = dpg.get_value(input_value01_tag)
        start_time = dpg.get_value(input_value02_tag)
        end_time = dpg.get_value(input_value02_tag + "_end")
        api_endpoint = dpg.get_value(input_value03_tag)

        if query and query.strip():
            try:
                result = self._execute_atlas_query(query, start_time, end_time, api_endpoint)
                if result:
                    print(f"Query executed successfully: {len(result.get('data', []))} time series")
                else:
                    print("Query failed - no data returned")
            except Exception as e:
                print(f"Query execution error: {e}")
        else:
            print("Please enter a valid Atlas query")

    def _execute_atlas_query(self, query: str, start_time: str, end_time: str, api_endpoint: str) -> Optional[Dict]:
        """Execute Atlas API query."""
        try:
            # Build Atlas API URL
            url = f"{api_endpoint}/api/v1/graph"

            # Prepare query parameters
            params = {
                'q': query,
                's': start_time,
                'e': end_time,
                'format': 'json'
            }

            # Add authentication if available
            headers = {}
            if self._auth_token:
                headers['Authorization'] = f'Bearer {self._auth_token}'

            # Execute request
            response = self._session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()

            # Parse response
            result = response.json()

            # Convert to our standard format
            processed_result = {
                'data': result.get('data', []),
                'metadata': {
                    'query': query,
                    'start': result.get('start', 0),
                    'end': result.get('end', 0),
                    'step': result.get('step', 60000),
                    'endpoint': api_endpoint
                }
            }

            return processed_result

        except requests.exceptions.RequestException as e:
            print(f"Atlas API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Failed to parse Atlas API response: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error executing Atlas query: {e}")
            return None

    def close(self, node_id: int) -> None:
        """Cleanup when node is deleted."""
        pass

    def get_setting_dict(self, node_id: int) -> Dict[str, Any]:
        """Return node configuration for saving."""
        tag_node_name = str(node_id) + ':' + self.node_tag
        input_value01_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input01Value'
        input_value02_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input02Value'
        input_value03_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input03Value'

        try:
            query = dpg.get_value(input_value01_tag)
            start_time = dpg.get_value(input_value02_tag)
            end_time = dpg.get_value(input_value02_tag + "_end")
            api_endpoint = dpg.get_value(input_value03_tag)
        except:
            query = self._query_string
            start_time = self._time_range['start']
            end_time = self._time_range['end']
            api_endpoint = self._api_endpoint

        pos = dpg.get_item_pos(tag_node_name)

        setting_dict = {
            'ver': self._ver,
            'pos': pos,
            'query': query,
            'start_time': start_time,
            'end_time': end_time,
            'api_endpoint': api_endpoint,
            'auth_token': self._auth_token
        }

        return setting_dict

    def set_setting_dict(self, node_id: int, setting_dict: Dict[str, Any]) -> None:
        """Restore node configuration from saved data."""
        tag_node_name = str(node_id) + ':' + self.node_tag
        input_value01_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input01Value'
        input_value02_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input02Value'
        input_value03_tag = tag_node_name + ':' + self.TYPE_TEXT + ':Input03Value'

        query = setting_dict.get('query', '')
        start_time = setting_dict.get('start_time', 'e-1h')
        end_time = setting_dict.get('end_time', 'now')
        api_endpoint = setting_dict.get('api_endpoint', 'http://localhost:7101')
        auth_token = setting_dict.get('auth_token', None)

        dpg.set_value(input_value01_tag, query)
        dpg.set_value(input_value02_tag, start_time)
        dpg.set_value(input_value02_tag + "_end", end_time)
        dpg.set_value(input_value03_tag, api_endpoint)

        self._query_string = query
        self._time_range = {'start': start_time, 'end': end_time}
        self._api_endpoint = api_endpoint
        self._auth_token = auth_token
