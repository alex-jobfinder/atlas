# Atlas

Backend for managing dimensional time series data.

## Links

* [Documentation](https://netflix.github.io/atlas-docs/)
* [Mailing List](https://groups.google.com/forum/#!forum/netflix-atlas)
* [Issues](https://github.com/Netflix/atlas/issues)
* [Releases](https://github.com/Netflix/atlas/releases)

## Python Local Chart Runner

For a minimal Python renderer that reads an Atlas test JSON and writes a PNG (no Atlas server needed), see:

- docs/python-local-chart-runner.md

## Atlas CLI Demo

To regenerate sample data and manifest and fetch a chart using the CLI:

```sh
python scripts/generate_demo_data.py
python scripts/mock_atlas_server.py &
python atlas_cli.py visualize multi-country-total --metric impressions --countries US --countries CA --include-total --output demo.png
```

The image will be written to `demo.png`.

## License

Copyright 2014-2025 Netflix, Inc.

Licensed under the Apache License, Version 2.0 (the “License”); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

```sh
#!/bin/bash
# Atlas Graph Style Templates Runner - Optimized Batch Version with Alert Visualizations
# Usage: ./run_all_styles_optimized_with_signal_line.sh [style_name]
#
# =============================================================================
# END-TO-END PROCESS DOCUMENTATION
# =============================================================================
#
# This script generates comprehensive Atlas graph visualizations that show:
# 1. Input time series data (in various styles: line, area, stack, etc.)
# 2. Alert threshold lines (horizontal reference lines)
# 3. Triggered alert zones (vertical spans when alerts fire)
#
# PROCESS FLOW:
# ┌─────────────────────────────────────────────────────────────────────────┐
# │                           ATLAS ALERT VISUALIZATION PIPELINE            │
# └─────────────────────────────────────────────────────────────────────────┘
#
# 1. DATA GENERATION
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  Synthetic Data → StaticDatabase → TimeSeries → Atlas Query Language   │
# │                                                                         │
# │  Preset "sps" → Small Dataset → CPU metrics by cluster → AQL Expression│
# │                                                                         │
# │  Example: name,sps,:eq,(,nf.cluster,),:by                              │
# │           ↓                                                             │
# │  Generates: Multiple time series with cluster tags                     │
# └─────────────────────────────────────────────────────────────────────────┘
#
# 2. ALERT EXPRESSION CONSTRUCTION
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  Base Query + Alert Logic + Visual Elements = Complete Expression     │
# │                                                                         │
# │  Input Data:    name,sps,:eq,(,nf.cluster,),:by                        │
# │  Alert Logic:   :sum,50e3,:2over,:gt,:vspan,40,:alpha                 │
# │  Visual Labels: triggered,:legend,:rot                                 │
# │  Threshold:     50e3,:const,threshold,:legend,:rot                    │
# │                                                                         │
# │  Final Expression:                                                     │
# │  [Alert Zones] + [Input Data] + [Threshold Line]                      │
# └─────────────────────────────────────────────────────────────────────────┘
#
# 3. VISUALIZATION COMPONENTS
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  Each chart contains THREE visual elements:                            │
# │                                                                         │
# │  🔴 TRIGGERED ZONES (Red Vertical Spans)                               │
# │     ┌─────────────────────────────────────────────────────────────┐    │
# │     │ ████  ████     ████  ████  ████  ████     ████  ████       │    │
# │     │ ████  ████     ████  ████  ████  ████     ████  ████       │    │
# │     │ ████  ████     ████  ████  ████  ████     ████  ████       │    │
# │     └─────────────────────────────────────────────────────────────┘    │
# │     Shows: When data exceeds threshold (50,000)                       │
# │                                                                         │
# │  📊 INPUT DATA (Original Time Series)                                 │
# │     ┌─────────────────────────────────────────────────────────────┐    │
# │     │     ╭─╮     ╭─╮     ╭─╮     ╭─╮     ╭─╮     ╭─╮             │    │
# │     │    ╱   ╲   ╱   ╲   ╱   ╲   ╱   ╲   ╱   ╲   ╱   ╲            │    │
# │     │   ╱     ╲ ╱     ╲ ╱     ╲ ╱     ╲ ╱     ╲ ╱     ╲           │    │
# │     └─────────────────────────────────────────────────────────────┘    │
# │     Shows: Original CPU data by cluster (line/area/stack style)        │
# │                                                                         │
# │  📏 THRESHOLD LINE (Horizontal Reference)                              │
# │     ┌─────────────────────────────────────────────────────────────┐    │
# │     │                                                             │    │
# │     │ ─────────────────────────────────────────────────────────── │    │
# │     │                                                             │    │
# │     └─────────────────────────────────────────────────────────────┘    │
# │     Shows: Alert threshold at 50,000                                 │
# └─────────────────────────────────────────────────────────────────────────┘
#
# 4. STYLE VARIATIONS
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  Each style applies the same alert pattern but with different rendering:│
# │                                                                         │
# │  LINE:     ────╱╲────╱╲────╱╲────╱╲────╱╲────╱╲────                    │
# │  AREA:     ████╱╲████╱╲████╱╲████╱╲████╱╲████╱╲████                    │
# │  STACK:    ████╱╲████╱╲████╱╲████╱╲████╱╲████╱╲████                    │
# │            ████╱╲████╱╲████╱╲████╱╲████╱╲████╱╲████                    │
# │  HEATMAP:  ████╱╲████╱╲████╱╲████╱╲████╱╲████╱╲████                    │
# │            ████╱╲████╱╲████╱╲████╱╲████╱╲████╱╲████                    │
# │                                                                         │
# │  All styles maintain the same alert visualization overlay               │
# └─────────────────────────────────────────────────────────────────────────┘
#
# 5. BATCH OPTIMIZATION
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  Traditional Approach:           Optimized Approach:                  │
# │                                                                         │
# │  sbt compile → run style1 → exit    sbt compile → run style1           │
# │  sbt compile → run style2 → exit    sbt compile → run style2           │
# │  sbt compile → run style3 → exit    sbt compile → run style3           │
# │  ...                                ...                                 │
# │  Total: ~2+ minutes                sbt compile → exit                  │
# │                                    Total: ~30 seconds                  │
# │                                                                         │
# │  Single build session with multiple runMain commands                   │
# └─────────────────────────────────────────────────────────────────────────┘
#
# 6. OUTPUT GENERATION
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  For each style, generates:                                            │
# │                                                                         │
# │  📊 PNG Chart:     target/manual/sps_[style]_with_alert.png            │
# │  📄 V2 JSON:       target/manual/sps_[style]_with_alert.v2.json.gz     │
# │                                                                         │
# │  Example outputs:                                                       │
# │  • sps_line_with_alert.png        (Line chart with alert zones)        │
# │  • sps_area_with_alert.png        (Area chart with alert zones)        │
# │  • sps_stack_with_alert.png       (Stack chart with alert zones)       │
# │  • sps_heatmap_with_alert.png     (Heatmap with alert zones)           │
# │  • sps_combination_with_alert.png (Combination with alert zones)        │
# └─────────────────────────────────────────────────────────────────────────┘
#
# 7. ALERT LOGIC EXPLANATION
# ┌─────────────────────────────────────────────────────────────────────────┐
# │  Atlas Query Language (AQL) Components:                               │
# │                                                                         │
# │  :sum          → Aggregate all cluster data                            │
# │  50e3          → Threshold value (50,000)                              │
# │  :2over        → Duplicate threshold for comparison                     │
# │  :gt           → Greater than comparison                               │
# │  :vspan        → Vertical span (red zones when triggered)              │
# │  40,:alpha     → 40% transparency for overlay                          │
# │  :legend,:rot  → Legend rotation for readability                       │
# │                                                                         │
# │  This creates visual feedback showing exactly when alerts would fire    │
# └─────────────────────────────────────────────────────────────────────────┘
#
# =============================================================================
# USAGE EXAMPLES
# =============================================================================
#
# Run all styles with alert visualizations:
#   ./scripts/run_all_styles_optimized_with_signal_line.sh
#
# Run specific style:
#   ./scripts/run_all_styles_optimized_with_signal_line.sh line
#
# Available styles: line, area, area_neg, stack, stack_neg, stack_pct,
#                   vspan, heatmap, combination, layering
#
# =============================================================================

STYLES_DIR="scripts/styles_with_signal_line"
OUTPUT_DIR="target/manual"

if [ ! -d "$STYLES_DIR" ]; then
    echo "Styles directory not found: $STYLES_DIR"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi

if [ -n "$1" ]; then
    # Run specific style
    STYLE_FILE="$STYLES_DIR/$1.args"
    if [ -f "$STYLE_FILE" ]; then
        echo "Running style: $1"
        ARGS=$(cat "$STYLE_FILE")
        sbt "project atlas-eval" "runMain com.netflix.atlas.eval.tools.LocalGraphRunner $ARGS"
    else
        echo "Style not found: $1"
        echo "Available styles:"
        ls "$STYLES_DIR"/*.args | sed "s|$STYLES_DIR/||" | sed "s|\.args||"
    fi
else
    # Create a batch file for sbt - much faster than individual builds
    BATCH_FILE=$(mktemp)

    echo "project atlas-eval" >> "$BATCH_FILE"

    echo "Running all Atlas graph styles with alert visualizations in optimized batch mode..."
    echo "This will show input, threshold, and triggering state on the same graph!"

    for style_file in "$STYLES_DIR"/*.args; do
        if [ -f "$style_file" ]; then
            style_name=$(basename "$style_file" .args)
            ARGS=$(cat "$style_file")
            echo "runMain com.netflix.atlas.eval.tools.LocalGraphRunner $ARGS" >> "$BATCH_FILE"
        fi
    done

    echo "exit" >> "$BATCH_FILE"

    # Run sbt in batch mode - single build, multiple runs
    time sbt < "$BATCH_FILE"

    # Clean up
    rm "$BATCH_FILE"

    echo ""
    echo "All styles with alert visualizations completed! Check target/manual/ for generated files."
    echo "Files: *_with_alert.png - Charts showing input, threshold, and triggering state"
fi
```
