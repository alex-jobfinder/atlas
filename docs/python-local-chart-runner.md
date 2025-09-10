# Python Local Chart Runner

This adds a tiny Python tool to render a PNG line chart directly from the V1-style JSON files used by the Scala chart tests (e.g., `atlas-chart/src/test/resources/graphengine/data/*.json`). No Atlas server is required.

Files:
- `src_python_gui/chart_from_json.py` — renderer and CLI (uses Pillow)
- `src_python_gui/EngineDataGenerator.py` — synthetic time‑series helpers and simple chart models
- `src_python_gui/atlas_graph_models.py` — GraphRequest/Theme model used to pass basic options

Quick start:

1) Install env (uv):
   - `make install`

2) Render from the bundled sample JSON (light theme):
   - `uv run python -m src_python_gui.chart_from_json --input atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json --output atlas-chart/target/manual/default_non_uniformly_drawn_spikes_py.png`

3) Render dark theme with a synthetic overlay wave:
   - `uv run python -m src_python_gui.chart_from_json -i atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json -o atlas-chart/target/manual/default_non_uniformly_drawn_spikes_py_dark.png --theme dark --overlay-wave`

Advanced options:

- `--style {line,area,stack}`: choose how to draw the series (default: line)
- `--axis-groups 0,1,0`: assign each series to an axis index (0 = left, 1 = right)
- `--ylabel-left 'Requests/sec' --ylabel-right 'Errors/sec'`: set axis labels

Makefile target:

```
make py-chart-from-json \
  PY_JSON_IN=atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json \
  PY_JSON_OUT=atlas-chart/target/manual/default_non_uniformly_drawn_spikes_py.png \
  THEME=light \
  OVERLAY=true \
  STYLE=area \
  AXIS_GROUPS=0,1 \
  YLABEL_LEFT='GC Time' \
  YLABEL_RIGHT='Synthetic'
```

Notes:
- The renderer is intentionally minimal (axes + polylines) for portability in tests.
- PNG will be written even for sparse/NaN datasets (NaNs are skipped).
- The optional synthetic overlay exercises EngineDataGenerator.
