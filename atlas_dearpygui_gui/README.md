# Atlas DearPyGui Visualizer

A visual node-based interface for Atlas time series data visualization, built using DearPyGui and adapted from the Image-Processing-Node-Editor architecture.

## Features

- **Visual Programming**: Drag-and-drop interface for building data analysis pipelines
- **Atlas Integration**: Direct connectivity to Atlas API and support for Atlas data formats
- **Real-time Visualization**: Interactive charts with zoom, pan, and real-time updates
- **Node-based Architecture**: Modular design with extensible node system
- **Configuration Persistence**: Save and load dashboard configurations

## Architecture

This application adapts the proven Image-Processing-Node-Editor architecture for time series data visualization:

- **AtlasNodeABC**: Abstract base class for all Atlas-specific nodes
- **AtlasNodeEditor**: Core node editor with Atlas-specific functionality
- **Node Categories**: Data sources, processing, visualization, dashboard, and export nodes
- **Topological Execution**: Dependency-based execution order for data processing

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Configure Atlas connection in `config/atlas_config.json`:
```json
{
  "api_endpoint": "http://your-atlas-server:7101",
  "auth_token": "your-auth-token-if-needed"
}
```

3. Run the application:
```bash
python main.py
```

## Usage

### Basic Workflow

1. **Add Data Source**: Drag an "Atlas API" or "JSON Import" node onto the canvas
2. **Configure Query**: Set up your Atlas query and time range
3. **Add Visualization**: Connect a "Line Chart" node to display the data
4. **Customize**: Adjust chart settings and styling
5. **Save**: Export your dashboard configuration

### Node Types

#### Data Sources
- **Atlas API**: Connect directly to Atlas API endpoints
- **JSON Import**: Import Atlas GraphDef JSON files (V1 and V2 formats)
- **CSV Data**: Load time series from CSV files (planned)

#### Visualization
- **Line Chart**: Interactive line charts with multiple series
- **Area Chart**: Stacked and filled area charts (planned)
- **Heatmap**: Time-based heatmap visualizations (planned)

#### Dashboard
- **Dashboard Layout**: Arrange multiple charts in grid layouts (planned)
- **Time Range Selector**: Interactive time range picker (planned)

#### Export
- **PNG Export**: Export charts as PNG images (planned)
- **PDF Export**: Export dashboards as PDF reports (planned)

## Configuration

### Atlas Configuration (`config/atlas_config.json`)

```json
{
  "api_endpoint": "http://localhost:7101",
  "auth_token": null,
  "default_time_range": {
    "start": "e-1h",
    "end": "now",
    "step": "60s"
  },
  "chart_settings": {
    "width": 800,
    "height": 400,
    "theme": "light"
  }
}
```

### Command Line Options

```bash
python main.py --help
```

- `--config`: Path to configuration file
- `--width`: Window width (default: 1280)
- `--height`: Window height (default: 720)
- `--theme`: UI theme (light/dark)
- `--use_debug_print`: Enable debug output
- `--unuse_async_draw`: Disable async drawing (for debugging)

## Development

### Adding New Nodes

1. Create a new node file in the appropriate category directory
2. Inherit from `AtlasNodeABC`
3. Implement required abstract methods:
   - `add_node()`: Create visual representation
   - `update()`: Process data and update outputs
   - `get_setting_dict()`: Return configuration for saving
   - `set_setting_dict()`: Restore configuration from saved data
   - `close()`: Cleanup when node is deleted

### Example Node Structure

```python
from atlas_node_abc import AtlasNodeABC

class Node(AtlasNodeABC):
    _ver = '0.0.1'
    node_label = 'My Node'
    node_tag = 'MyNode'

    def add_node(self, parent, node_id, pos=[0, 0], atlas_config=None, callback=None):
        # Create visual representation
        pass

    def update(self, node_id, connection_list, node_data_dict, node_result_dict):
        # Process data and return results
        pass

    # ... implement other required methods
```

## Integration with Atlas

This application integrates directly with Atlas's core components:

- **TimeSeries Model**: Compatible with Atlas time series data structures
- **GraphDef Format**: Support for Atlas chart definitions
- **Query Language**: Full Atlas Query Language (AQL) support
- **API Endpoints**: Direct connectivity to Atlas API endpoints

## Roadmap

### Phase 1 (Current)
- ✅ Core architecture adaptation
- ✅ Basic Atlas data integration
- ✅ Essential data source nodes
- ✅ Simple line chart visualization

### Phase 2 (Planned)
- 🔄 Advanced visualization nodes (area, heatmap, alerts)
- 🔄 Time range selection and filtering
- 🔄 Query builder interface
- 🔄 Export functionality

### Phase 3 (Future)
- 🔄 Dashboard layout system
- 🔄 Real-time streaming updates
- 🔄 Alert and notification system
- 🔄 Plugin architecture for custom nodes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project follows the same license as the Atlas project.

## Acknowledgments

- Based on the Image-Processing-Node-Editor architecture by Kazuhito00
- Built on the DearPyGui framework
- Integrates with Netflix Atlas monitoring system
