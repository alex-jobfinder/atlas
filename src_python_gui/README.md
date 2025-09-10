Python Atlas Chart Renderer (Local Data)

This directory contains a minimal Python renderer to generate PNG charts from local JSON data, without running the Atlas server. It mirrors a subset of features from the Scala ChartRenderRunner and the PngGraphEngineSuite test helpers.

Key modules:
- atlas_graph_models.py: Enums and models for Atlas Graph API parameters.
- EngineDataGenerator.py: Helpers to synthesize time series data (constant, wave, intervals) and a lightweight chart data model.
- chart_from_json.py: CLI and function to render a PNG from a V1-style test JSON.

Usage

Render a PNG from an Atlas V1-style JSON:

```bash
python -m src_python_gui.chart_from_json \
  --input atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json \
  --output atlas-chart/target/manual/default_non_uniformly_drawn_spikes_py.png \
  --theme light \
  --width 700 --height 200
```

Overlay a synthetic wave series and render as area:

```bash
python -m src_python_gui.chart_from_json \
  --input atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json \
  --output atlas-chart/target/manual/default_non_uniformly_drawn_spikes_py_area.png \
  --overlay-wave --style area
```

Makefile

Use the chart-runner-py target to render the bundled sample via Python:

```bash
make chart-runner-py \
  RUNNER_IN=atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json \
  RUNNER_OUTPREFIX=atlas-chart/target/manual/default_non_uniformly_drawn_spikes_py
```

Tests

Run pytest to validate the renderer:

```bash
pytest -q
```

The test will render a small PNG from a sample JSON and assert the file exists and is non-empty.
