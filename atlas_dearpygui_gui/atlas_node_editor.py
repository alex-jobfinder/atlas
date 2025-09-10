#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Atlas Node Editor Core
Adapted from Image-Processing-Node-Editor for Atlas time series visualization
"""

import os
import copy
import json
import platform
import datetime
from glob import glob
from collections import OrderedDict
from importlib import import_module
from typing import Dict, List, Optional, Any
from pathlib import Path

import dearpygui.dearpygui as dpg
import pandas as pd
import numpy as np


class AtlasNodeEditor(object):
    """
    Core node editor for Atlas time series visualization.
    Adapted from DpgNodeEditor for Atlas-specific functionality.
    """

    _ver = '0.0.1'

    _node_editor_tag = 'AtlasNodeEditor'
    _node_editor_label = 'Atlas Time Series Editor'

    _node_id = 0
    _node_instance_list = {}
    _node_list = []
    _node_link_list = []
    _last_pos = None
    _terminate_flag = False
    _atlas_config = None
    _use_debug_print = False

    def __init__(
        self,
        width: int = 1280,
        height: int = 720,
        pos: List[int] = [0, 0],
        atlas_config: Optional[Dict] = None,
        node_dir: str = 'atlas_nodes',
        menu_dict: Optional[Dict] = None,
        use_debug_print: bool = False,
    ):
        """Initialize the Atlas node editor."""
        # Various initialization
        self._node_id = 0
        self._node_instance_list = {}
        self._node_list = []
        self._node_link_list = []
        self._node_connection_dict = OrderedDict([])
        self._use_debug_print = use_debug_print
        self._terminate_flag = False
        self._atlas_config = atlas_config or {}

        # Menu item definition (key: menu name, value: node code storage directory name)
        if menu_dict is None:
            menu_dict = OrderedDict({
                'Data Sources': 'data_sources',
                'Processing': 'processing',
                'Visualization': 'visualization',
                'Dashboard': 'dashboard',
                'Export': 'export'
            })

        # File dialog setup
        datetime_now = datetime.datetime.now()
        with dpg.file_dialog(
                directory_selector=False,
                show=False,
                modal=True,
                height=int(height / 2),
                default_filename=f"atlas_dashboard_{datetime_now.strftime('%Y%m%d')}",
                callback=self._callback_file_export,
                id='atlas_file_export',
        ):
            dpg.add_file_extension('.json')
            dpg.add_file_extension('', color=(150, 255, 150, 255))

        with dpg.file_dialog(
                directory_selector=False,
                show=False,
                modal=True,
                height=int(height / 2),
                callback=self._callback_file_import,
                id='atlas_file_import',
        ):
            dpg.add_file_extension('.json')
            dpg.add_file_extension('', color=(150, 255, 150, 255))

        # Atlas node editor window generation
        with dpg.window(
                tag=self._node_editor_tag + 'Window',
                label=self._node_editor_label,
                width=width,
                height=height,
                pos=pos,
                menubar=True,
                on_close=self._callback_close_window,
        ):
            # Menu bar generation
            with dpg.menu_bar(label='AtlasMenuBar'):
                # File menu
                with dpg.menu(label='File'):
                    dpg.add_menu_item(
                        tag='Menu_File_Export',
                        label='Export Dashboard',
                        callback=self._callback_file_export_menu,
                        user_data='Menu_File_Export',
                    )
                    dpg.add_menu_item(
                        tag='Menu_File_Import',
                        label='Import Dashboard',
                        callback=self._callback_file_import_menu,
                        user_data='Menu_File_Import',
                    )
                    dpg.add_separator()
                    dpg.add_menu_item(
                        tag='Menu_File_New',
                        label='New Dashboard',
                        callback=self._callback_new_dashboard,
                    )

                # Atlas-specific menu
                with dpg.menu(label='Atlas'):
                    dpg.add_menu_item(
                        tag='Menu_Atlas_Config',
                        label='Atlas Configuration',
                        callback=self._callback_atlas_config,
                    )
                    dpg.add_menu_item(
                        tag='Menu_Atlas_Theme',
                        label='Toggle Theme',
                        callback=self._callback_toggle_theme,
                    )
                    dpg.add_menu_item(
                        tag='Menu_Atlas_Refresh',
                        label='Refresh Data',
                        callback=self._callback_refresh_data,
                    )

                # Node menu generation
                for menu_info in menu_dict.items():
                    menu_label = menu_info[0]

                    with dpg.menu(label=menu_label):
                        # Node code storage path generation
                        node_sources_path = str(Path(node_dir) / menu_info[1] / '*.py')

                        # Get list of node codes in specified directory
                        node_sources = glob(node_sources_path)
                        for node_source in node_sources:
                            # Generate path for dynamic import
                            node_path = Path(node_source)
                            import_path = str(node_path.with_suffix(''))
                            # Convert path separators to dots for module import
                            import_path = import_path.replace(os.sep, '.')

                            import_path = import_path.split('.')
                            import_path = '.'.join(import_path[-3:])
                            # Exclude __init__.py only
                            if import_path.endswith('__init__'):
                                continue

                            # Dynamic import module
                            try:
                                module = import_module(import_path)

                                # Generate node instance
                                node = module.Node()

                                # Add menu item
                                dpg.add_menu_item(
                                    tag='Menu_' + node.node_tag,
                                    label=node.node_label,
                                    callback=self._callback_add_node,
                                    user_data=node.node_tag,
                                )

                                # Add to instance list
                                self._node_instance_list[node.node_tag] = node
                            except Exception as e:
                                if self._use_debug_print:
                                    print(f"Failed to load node {import_path}: {e}")

            # Node editor generation (initial state: no nodes added)
            with dpg.node_editor(
                    tag=self._node_editor_tag,
                    callback=self._callback_link,
                    minimap=True,
                    minimap_location=dpg.mvNodeMiniMap_Location_BottomRight,
            ):
                pass

            # Import restriction popup
            with dpg.window(
                    label='Import Restriction',
                    modal=True,
                    show=False,
                    id='modal_atlas_file_import',
                    no_title_bar=True,
                    pos=[52, 52],
            ):
                dpg.add_text(
                    'Atlas dashboard import works only before adding nodes.\n'
                    'Please clear the canvas before importing.',
                )
                dpg.add_separator()
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label='OK',
                        width=375,
                        callback=lambda: dpg.configure_item(
                            'modal_atlas_file_import',
                            show=False,
                        ),
                    )

            # Mouse and keyboard callback registration
            with dpg.handler_registry():
                dpg.add_mouse_click_handler(
                    callback=self._callback_save_last_pos)
                dpg.add_key_press_handler(
                    dpg.mvKey_Delete,
                    callback=self._callback_mv_key_del,
                )

    def get_node_list(self) -> List[str]:
        """Get list of active nodes."""
        return self._node_list

    def get_sorted_node_connection(self) -> OrderedDict:
        """Get sorted node connections."""
        return self._node_connection_dict

    def get_node_instance(self, node_name: str):
        """Get node instance by name."""
        return self._node_instance_list.get(node_name, None)

    def set_terminate_flag(self, flag: bool = True) -> None:
        """Set termination flag."""
        self._terminate_flag = flag

    def get_terminate_flag(self) -> bool:
        """Get termination flag."""
        return self._terminate_flag

    def _callback_add_node(self, sender, data, user_data):
        """Callback for adding a new node."""
        self._node_id += 1

        # Get node instance
        node = self._node_instance_list[user_data]

        # Add node to editor
        last_pos = [0, 0]
        if self._last_pos is not None:
            last_pos = [self._last_pos[0] + 30, self._last_pos[1] + 30]

        tag_name = node.add_node(
            self._node_editor_tag,
            self._node_id,
            pos=last_pos,
            atlas_config=self._atlas_config,
        )

        self._node_list.append(tag_name)

        if self._use_debug_print:
            print('**** _callback_add_node ****')
            print(f'    Node ID         : {self._node_id}')
            print(f'    sender          : {sender}')
            print(f'    data            : {data}')
            print(f'    user_data       : {user_data}')
            print(f'    self._node_list : {", ".join(self._node_list)}')
            print()

    def _callback_link(self, sender, data):
        """Callback for linking nodes."""
        # Get types of each connection
        source = dpg.get_item_alias(data[0])
        destination = dpg.get_item_alias(data[1])
        source_type = source.split(':')[2]
        destination_type = destination.split(':')[2]

        # Process only if types match
        if source_type == destination_type:
            # First node generation
            if len(self._node_link_list) == 0:
                dpg.add_node_link(source, destination, parent=sender)
                self._node_link_list.append([source, destination])
            # Second time onwards
            else:
                # Check if input port doesn't have multiple connections
                duplicate_flag = False
                for node_link in self._node_link_list:
                    if destination == node_link[1]:
                        duplicate_flag = True
                if not duplicate_flag:
                    dpg.add_node_link(source, destination, parent=sender)
                    self._node_link_list.append([source, destination])

        # Regenerate node graph
        self._node_connection_dict = self._sort_node_graph(
            self._node_list,
            self._node_link_list,
        )

        if self._use_debug_print:
            print('**** _callback_link ****')
            print(f'    sender                     : {sender}')
            print(f'    data                       : {data}')
            print(f'    self._node_list            : {self._node_list}')
            print(f'    self._node_link_list       : {self._node_link_list}')
            print(f'    self._node_connection_dict : {self._node_connection_dict}')
            print()

    def _callback_close_window(self, sender):
        """Callback for closing window."""
        dpg.delete_item(sender)

    def _sort_node_graph(self, node_list: List[str], node_link_list: List[List[str]]) -> OrderedDict:
        """Sort node graph for proper execution order."""
        node_id_dict = OrderedDict({})
        node_connection_dict = OrderedDict({})

        # Organize node IDs and connections in dictionary format
        for node_link_info in node_link_list:
            source = dpg.get_item_alias(node_link_info[0])
            destination = dpg.get_item_alias(node_link_info[1])
            source_id = int(source.split(':')[0])
            destination_id = int(destination.split(':')[0])

            if destination_id not in node_id_dict:
                node_id_dict[destination_id] = [source_id]
            else:
                node_id_dict[destination_id].append(source_id)

            split_destination = destination.split(':')
            node_name = split_destination[0] + ':' + split_destination[1]

            if node_name not in node_connection_dict:
                node_connection_dict[node_name] = [[source, destination]]
            else:
                node_connection_dict[node_name].append([source, destination])

        node_id_list = list(node_id_dict.items())
        node_connection_list = list(node_connection_dict.items())

        # Swap processing order from input to output
        index = 0
        while index < len(node_id_list):
            swap_flag = False
            for check_id in node_id_list[index][1]:
                for check_index in range(index + 1, len(node_id_list)):
                    if node_id_list[check_index][0] == check_id:
                        node_id_list[check_index], node_id_list[index] = node_id_list[index], node_id_list[check_index]
                        node_connection_list[check_index], node_connection_list[index] = node_connection_list[index], node_connection_list[check_index]
                        swap_flag = True
                        break
            if not swap_flag:
                index += 1

        # Add nodes that don't appear in connection list (input nodes, etc.)
        index = 0
        unfinded_id_dict = {}
        while index < len(node_id_list):
            for check_id in node_id_list[index][1]:
                check_index = 0
                find_flag = False
                while check_index < len(node_id_list):
                    if check_id == node_id_list[check_index][0]:
                        find_flag = True
                        break
                    check_index += 1
                if not find_flag:
                    for index, node_id_name in enumerate(node_list):
                        node_id, node_name = node_id_name.split(':')
                        if node_id == check_id:
                            unfinded_id_dict[check_id] = node_id_name
                            break
            index += 1

        for unfinded_value in unfinded_id_dict.values():
            node_connection_list.insert(0, (unfinded_value, []))

        return OrderedDict(node_connection_list)

    def _callback_file_export(self, sender, data):
        """Callback for file export."""
        setting_dict = {}

        # Save node list and connection list
        setting_dict['node_list'] = self._node_list
        setting_dict['link_list'] = self._node_link_list
        setting_dict['atlas_config'] = self._atlas_config

        # Save settings for each node
        for node_id_name in self._node_list:
            node_id, node_name = node_id_name.split(':')
            node = self._node_instance_list[node_name]

            setting = node.get_setting_dict(node_id)

            setting_dict[node_id_name] = {
                'id': str(node_id),
                'name': str(node_name),
                'setting': setting
            }

        # Write to JSON file
        with open(data['file_path_name'], 'w') as fp:
            json.dump(setting_dict, fp, indent=4)

        if self._use_debug_print:
            print('**** _callback_file_export ****')
            print(f'    sender          : {sender}')
            print(f'    data            : {data}')
            print(f'    setting_dict    : {setting_dict}')
            print()

    def _callback_file_export_menu(self):
        """Callback for file export menu."""
        dpg.show_item('atlas_file_export')

    def _callback_file_import_menu(self):
        """Callback for file import menu."""
        if self._node_id == 0:
            dpg.show_item('atlas_file_import')
        else:
            dpg.configure_item('modal_atlas_file_import', show=True)

    def _callback_file_import(self, sender, data):
        """Callback for file import."""
        if data['file_name'] != '.':
            # Load from JSON file
            setting_dict = None
            with open(data['file_path_name']) as fp:
                setting_dict = json.load(fp)

            # Restore settings for each node
            for node_id_name in setting_dict['node_list']:
                node_id, node_name = node_id_name.split(':')
                node = self._node_instance_list[node_name]

                node_id = int(node_id)

                if node_id > self._node_id:
                    self._node_id = node_id

                # Get node instance
                node = self._node_instance_list[node_name]

                # Version warning
                ver = setting_dict[node_id_name]['setting']['ver']
                if ver != node._ver:
                    warning_node_name = setting_dict[node_id_name]['name']
                    print(f'WARNING : {warning_node_name} is different version')
                    print(f'                     Load Version -> {ver}')
                    print(f'                     Code Version -> {node._ver}')
                    print()

                # Add node to editor
                pos = setting_dict[node_id_name]['setting']['pos']
                node.add_node(
                    self._node_editor_tag,
                    node_id,
                    pos=pos,
                    atlas_config=self._atlas_config,
                )

                # Restore settings
                node.set_setting_dict(
                    node_id,
                    setting_dict[node_id_name]['setting'],
                )

            # Restore node list and connection list
            self._node_list = setting_dict['node_list']
            self._node_link_list = setting_dict['link_list']

            # Restore Atlas configuration
            if 'atlas_config' in setting_dict:
                self._atlas_config = setting_dict['atlas_config']

            # Restore node connections
            for node_link in self._node_link_list:
                dpg.add_node_link(
                    node_link[0],
                    node_link[1],
                    parent=self._node_editor_tag,
                )

            # Regenerate node graph
            self._node_connection_dict = self._sort_node_graph(
                self._node_list,
                self._node_link_list,
            )

        if self._use_debug_print:
            print('**** _callback_file_import ****')
            print(f'    sender          : {sender}')
            print(f'    data            : {data}')
            print(f'    setting_dict    : {setting_dict}')
            print()

    def _callback_save_last_pos(self):
        """Callback for saving last position."""
        if len(dpg.get_selected_nodes(self._node_editor_tag)) > 0:
            self._last_pos = dpg.get_item_pos(
                dpg.get_selected_nodes(self._node_editor_tag)[0])

    def _callback_mv_key_del(self):
        """Callback for delete key."""
        if len(dpg.get_selected_nodes(self._node_editor_tag)) > 0:
            # Get item ID of selected node
            item_id = dpg.get_selected_nodes(self._node_editor_tag)[0]
            # Identify node name
            node_id_name = dpg.get_item_alias(item_id)
            node_id, node_name = node_id_name.split(':')

            # Node cleanup
            node_instance = self.get_node_instance(node_name)
            node_instance.close(node_id)
            # Remove from node list
            self._node_list.remove(node_id_name)
            # Remove from node link list
            copy_node_link_list = copy.deepcopy(self._node_link_list)
            for link_info in copy_node_link_list:
                source_node = link_info[0].split(':')[:2]
                source_node = ':'.join(source_node)
                destination_node = link_info[1].split(':')[:2]
                destination_node = ':'.join(destination_node)

                if source_node == node_id_name or destination_node == node_id_name:
                    self._node_link_list.remove(link_info)

            # Regenerate node graph
            self._node_connection_dict = self._sort_node_graph(
                self._node_list,
                self._node_link_list,
            )

            # Delete item
            dpg.delete_item(item_id)

        if len(dpg.get_selected_links(self._node_editor_tag)) > 0:
            self._node_link_list.remove([
                dpg.get_item_alias(dpg.get_item_configuration(dpg.get_selected_links(self._node_editor_tag)[0])['attr_1']),
                dpg.get_item_alias(dpg.get_item_configuration(dpg.get_selected_links(self._node_editor_tag)[0])['attr_2'])
            ])

            self._node_connection_dict = self._sort_node_graph(
                self._node_list,
                self._node_link_list,
            )

            dpg.delete_item(dpg.get_selected_links(self._node_editor_tag)[0])

        if self._use_debug_print:
            print('**** _callback_mv_key_del ****')
            print(f'    self._node_list            : {self._node_list}')
            print(f'    self._node_link_list       : {self._node_link_list}')
            print(f'    self._node_connection_dict : {self._node_connection_dict}')

    def _callback_new_dashboard(self):
        """Callback for new dashboard."""
        # Clear all nodes
        for node_id_name in self._node_list:
            node_id, node_name = node_id_name.split(':')
            node_instance = self.get_node_instance(node_name)
            node_instance.close(node_id)

        self._node_list = []
        self._node_link_list = []
        self._node_connection_dict = OrderedDict([])

        # Clear the node editor
        dpg.delete_item(self._node_editor_tag, children_only=True)

    def _callback_atlas_config(self):
        """Callback for Atlas configuration."""
        # TODO: Implement Atlas configuration dialog
        print("Atlas configuration dialog not yet implemented")

    def _callback_toggle_theme(self):
        """Callback for toggling theme."""
        # TODO: Implement theme toggle
        print("Theme toggle not yet implemented")

    def _callback_refresh_data(self):
        """Callback for refreshing data."""
        # TODO: Implement data refresh
        print("Data refresh not yet implemented")
