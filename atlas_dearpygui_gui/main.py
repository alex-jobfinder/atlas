#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Atlas DearPyGui Main Application
Visual node-based interface for Atlas time series data visualization
Adapted from Image-Processing-Node-Editor architecture
"""

import sys
import copy
import json
import asyncio
import argparse
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Optional

import dearpygui.dearpygui as dpg

# Add current directory to path for imports
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

try:
    from atlas_node_editor import AtlasNodeEditor
    from themes import apply_theme
except ImportError as e:
    print(f"Error: Could not import AtlasNodeEditor: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    sys.exit(1)


def get_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Atlas DearPyGui Visualizer")

    parser.add_argument(
        "--config",
        type=str,
        default=str(Path(__file__).parent / 'config' / 'atlas_config.json'),
        help="Path to Atlas configuration file"
    )
    parser.add_argument(
        "--unuse_async_draw",
        action="store_true",
        help="Disable async drawing (for debugging)"
    )
    parser.add_argument(
        "--use_debug_print",
        action="store_true",
        help="Enable debug output"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Window width"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Window height"
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="light",
        choices=["light", "dark"],
        help="UI theme"
    )

    return parser.parse_args()


def async_main(node_editor):
    """Async main loop for node processing."""
    # Data containers for node processing results
    node_data_dict = {}
    node_result_dict = {}

    # Main loop
    while not node_editor.get_terminate_flag():
        update_node_info(node_editor, node_data_dict, node_result_dict)


def update_node_info(
    node_editor,
    node_data_dict: Dict,
    node_result_dict: Dict,
    mode_async: bool = True,
):
    """Update node information and process data."""
    # Get node list
    node_list = node_editor.get_node_list()

    # Get node connection information
    sorted_node_connection_dict = node_editor.get_sorted_node_connection()

    # Update information for each node
    for node_id_name in node_list:
        if node_id_name not in node_data_dict:
            node_data_dict[node_id_name] = None

        node_id, node_name = node_id_name.split(':')
        connection_list = sorted_node_connection_dict.get(node_id_name, [])

        # Get node instance by name
        node_instance = node_editor.get_node_instance(node_name)

        # Update specified node information
        if mode_async:
            try:
                data, result = node_instance.update(
                    node_id,
                    connection_list,
                    node_data_dict,
                    node_result_dict,
                )
            except Exception as e:
                print(f"Node update error: {e}")
                continue
        else:
            data, result = node_instance.update(
                node_id,
                connection_list,
                node_data_dict,
                node_result_dict,
            )

        node_data_dict[node_id_name] = copy.deepcopy(data)
        node_result_dict[node_id_name] = copy.deepcopy(result)


def load_atlas_config(config_path: str) -> Dict:
    """Load Atlas configuration from JSON file."""
    default_config = {
        "api_endpoint": "http://localhost:7101",
        "auth_token": None,
        "default_time_range": {
            "start": "e-1h",
            "end": "now",
            "step": "60s"
        },
        "chart_settings": {
            "width": 800,
            "height": 400,
            "theme": "light"
        },
        "node_settings": {
            "default_width": 200,
            "default_height": 150
        }
    }

    config_file = Path(config_path)
    if config_file.exists():
        try:
            with config_file.open('r') as f:
                config = json.load(f)
            # Merge with defaults
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
        except Exception as e:
            print(f"Warning: Could not load config file {config_path}: {e}")
            print("Using default configuration")

    return default_config


def initialize_default_view(node_editor: AtlasNodeEditor, atlas_config: Dict) -> None:
    """Create a default node setup with sample data and chart."""
    default_cfg = atlas_config.get("default_dataset", {})
    if not (default_cfg.get("enabled") and default_cfg.get("auto_load")):
        return

    dataset_node = node_editor.get_node_instance("DefaultDataset")
    chart_node = node_editor.get_node_instance("LineChart")
    if not dataset_node or not chart_node:
        return

    # Add default dataset node
    node_editor._node_id += 1
    dataset_tag = dataset_node.add_node(
        node_editor._node_editor_tag,
        node_editor._node_id,
        pos=[20, 20],
        atlas_config=atlas_config,
    )
    node_editor._node_list.append(dataset_tag)

    # Add line chart node
    node_editor._node_id += 1
    chart_tag = chart_node.add_node(
        node_editor._node_editor_tag,
        node_editor._node_id,
        pos=[350, 20],
        atlas_config=atlas_config,
    )
    node_editor._node_list.append(chart_tag)

    # Link dataset to chart
    source_attr = f"{dataset_tag}:{dataset_node.TYPE_TIME_SERIES}:Output01"
    dest_attr = f"{chart_tag}:{chart_node.TYPE_TIME_SERIES}:Input01"
    dpg.add_node_link(source_attr, dest_attr, parent=node_editor._node_editor_tag)
    node_editor._node_link_list.append([source_attr, dest_attr])
    node_editor._node_connection_dict = node_editor._sort_node_graph(
        node_editor._node_list, node_editor._node_link_list
    )

    # Pre-render once so chart appears on launch
    node_data_dict: Dict = {}
    node_result_dict: Dict = {}
    update_node_info(node_editor, node_data_dict, node_result_dict, mode_async=False)


def main():
    """Main application entry point."""
    args = get_args()
    config_path = args.config
    unuse_async_draw = args.unuse_async_draw
    use_debug_print = args.use_debug_print
    window_width = args.width
    window_height = args.height
    theme = args.theme

    # Load Atlas configuration
    print('**** Load Atlas Configuration ********')
    atlas_config = load_atlas_config(config_path)

    # Create config directory if it doesn't exist
    config_file = Path(config_path)
    config_dir = config_file.parent
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        # Save default config
        with config_file.open('w') as f:
            json.dump(atlas_config, f, indent=2)

    # DearPyGui setup (context creation, setup, viewport creation)
    editor_width = window_width
    editor_height = window_height

    print('**** DearPyGui Setup ********')
    dpg.create_context()
    dpg.setup_dearpygui()
    dpg.create_viewport(
        title="Atlas Time Series Visualizer",
        width=editor_width,
        height=editor_height,
    )

    # Set theme using simplified theme system
    apply_theme(theme)

    # Create Atlas node editor
    print('**** Create Atlas Node Editor ********')
    menu_dict = OrderedDict({
        'Data Sources': 'data_sources',
        'Processing': 'processing',
        'Visualization': 'visualization',
        'Dashboard': 'dashboard',
        'Export': 'export'
    })

    node_editor = AtlasNodeEditor(
        width=editor_width - 15,
        height=editor_height - 40,
        atlas_config=atlas_config,
        menu_dict=menu_dict,
        use_debug_print=use_debug_print,
        node_dir=str(Path(__file__).parent / 'atlas_nodes'),
    )

    # Initialize default dataset and chart if configured
    initialize_default_view(node_editor, atlas_config)

    # Show viewport
    dpg.show_viewport()

    # Main loop
    print('**** Start Main Event Loop ********')
    if not unuse_async_draw:
        try:
            # Try to get existing event loop
            event_loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, create a new one
            event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(event_loop)

        event_loop.run_in_executor(None, async_main, node_editor)
        dpg.start_dearpygui()
    else:
        # Data containers for node processing results
        node_data_dict = {}
        node_result_dict = {}
        while dpg.is_dearpygui_running():
            update_node_info(
                node_editor,
                node_data_dict,
                node_result_dict,
                mode_async=False,
            )
            dpg.render_dearpygui_frame()

    # Cleanup
    print('**** Terminate process ********')
    # Cleanup for each node
    print('**** Close All Nodes ********')
    node_list = node_editor.get_node_list()
    for node_id_name in node_list:
        node_id, node_name = node_id_name.split(':')
        node_instance = node_editor.get_node_instance(node_name)
        node_instance.close(node_id)

    # Stop event loop
    print('**** Stop Event Loop ********')
    node_editor.set_terminate_flag()
    if not unuse_async_draw:
        event_loop.stop()

    # Destroy DearPyGui context
    print('**** Destroy DearPyGui Context ********')
    dpg.destroy_context()


if __name__ == '__main__':
    main()
