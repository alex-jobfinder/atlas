#!/bin/bash
# Atlas Graph Style Templates Runner - Optimized Batch Version with Alert Visualizations
# Usage: ./run_all_styles.sh [style_name]
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
# │  📊 PNG Chart:     scripts_png_gen/output/sps_[style]_with_alert.png            │
# │  📄 V2 JSON:       scripts_png_gen/output/sps_[style]_with_alert.v2.json.gz     │
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
#   ./scripts_png_gen/run_all_styles.sh
#
# Run specific style:
#   ./scripts_png_gen/run_all_styles.sh line
#
# Available styles: line, area, area_neg, stack, stack_neg, stack_pct,
#                   vspan, heatmap, combination, layering
#
# =============================================================================

STYLES_DIR="scripts_png_gen/input_args/styles_all/args"
OUTPUT_DIR="scripts_png_gen/output/styles_all"

if [ ! -d "$STYLES_DIR" ]; then
    echo "Styles directory not found: $STYLES_DIR"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi

if [ -n "$1" ]; then
    # Run matching subset (by substring) or a specific args file path
    MATCHED_FILES=$(find "$STYLES_DIR" -type f -name "*$1*.args" | sort)
    if [ -z "$MATCHED_FILES" ] && [ -f "$1" ]; then
        MATCHED_FILES="$1"
    fi
    if [ -n "$MATCHED_FILES" ]; then
        BATCH_FILE=$(mktemp)
        echo "project atlas-eval" >> "$BATCH_FILE"
        echo "Running selected styles matching: $1"
        while IFS= read -r style_file; do
            [ -f "$style_file" ] || continue
            ARGS=$(cat "$style_file")
            echo "runMain com.netflix.atlas.eval.tools.LocalGraphRunner $ARGS" >> "$BATCH_FILE"
        done <<< "$MATCHED_FILES"
        echo "exit" >> "$BATCH_FILE"
        time sbt < "$BATCH_FILE"
        rm "$BATCH_FILE"
    else
        echo "No matching .args for: $1"
        echo "Examples:"
        find "$STYLES_DIR" -type f -name "*.args" | head -n 30 | sed "s|^$STYLES_DIR/||"
    fi
else
    # Create a batch file for sbt - much faster than individual builds
    BATCH_FILE=$(mktemp)

    echo "project atlas-eval" >> "$BATCH_FILE"

    echo "Running all Atlas graph styles with alert visualizations in optimized batch mode..."
    echo "This will show input, threshold, and triggering state on the same graph!"

    while IFS= read -r style_file; do
        [ -f "$style_file" ] || continue
        ARGS=$(cat "$style_file")
        echo "runMain com.netflix.atlas.eval.tools.LocalGraphRunner $ARGS" >> "$BATCH_FILE"
    done < <(find "$STYLES_DIR" -type f -name "*.args" | sort)

    echo "exit" >> "$BATCH_FILE"

    # Run sbt in batch mode - single build, multiple runs
    time sbt < "$BATCH_FILE"

    # Clean up
    rm "$BATCH_FILE"

    echo ""
    echo "All styles with alert visualizations completed! Check scripts_png_gen/output/ for generated files."
    echo "Files: *_with_alert.png - Charts showing input, threshold, and triggering state"
fi
# chmod +x scripts_png_gen/run_all_styles_optimized_with_signal_line.sh
# ./scripts_png_gen/run_all_styles.sh
# ./scripts_png_gen/run_all_styles.sh line

# chmod +x scripts_png_gen/atlas_cli_helper.sh
# chmod +x scripts_png_gen/meta-iam-url.sh
# chmod +x scripts_png_gen/publish-test.sh
# chmod +x scripts_png_gen/run_all_styles.sh
# chmod +x scripts_png_gen/run_all_styles_optimized.sh
# chmod +x scripts_png_gen/run_visual_alerts.sh
# chmod +x scripts_png_gen/run_all_styles.sh
# chmod +x scripts_png_gen/write-aws-credentials.sh

# source "$HOME/.sdkman/bin/sdkman-init.sh" && sdk install java 17.0.12-tem && sdk use java 17.0.12-tem && java -version && export JAVA_TOOL_OPTIONS="-Djava.awt.headless=true" && cd /home/alex/dbt_ads/atlas && sbt "atlas-chart/testOnly com.netflix.atlas.chart.DefaultGraphEngineSuite -- -z heatmap_basic" | cat