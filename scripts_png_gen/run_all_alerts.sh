#!/bin/bash
# Atlas Alert Runner - Optimized Batch Version
# Usage: ./run_all_alerts.sh [alert_name]

ALERTS_DIR="scripts_png_gen/input_args/alerts"
OUTPUT_DIR="scripts_png_gen/output/alerts"

if [ ! -d "$ALERTS_DIR" ]; then
    echo "Alerts directory not found: $ALERTS_DIR"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi

if [ -n "$1" ]; then
    # Run specific alert
    ALERT_FILE="$ALERTS_DIR/$1.args"
    if [ -f "$ALERT_FILE" ]; then
        echo "Running alert: $1"
        ARGS=$(cat "$ALERT_FILE")
        sbt "project atlas-eval" "runMain com.netflix.atlas.eval.tools.LocalAlertRunner $ARGS"
    else
        echo "Alert not found: $1"
        echo "Available alerts:"
        ls "$ALERTS_DIR"/*.args | sed "s|$ALERTS_DIR/||" | sed "s|\.args||"
    fi
else
    # Create a batch file for sbt - much faster than individual builds
    BATCH_FILE=$(mktemp)

    echo "project atlas-eval" >> "$BATCH_FILE"

    echo "Running all Atlas alert scenarios in optimized batch mode..."
    echo "This will be much faster than individual builds!"

    for alert_file in "$ALERTS_DIR"/*.args; do
        if [ -f "$alert_file" ]; then
            alert_name=$(basename "$alert_file" .args)
            ARGS=$(cat "$alert_file")
            echo "runMain com.netflix.atlas.eval.tools.LocalAlertRunner $ARGS" >> "$BATCH_FILE"
        fi
    done

    echo "exit" >> "$BATCH_FILE"

    # Run sbt in batch mode - single build, multiple runs
    time sbt < "$BATCH_FILE"

    # Clean up
    rm "$BATCH_FILE"

    echo ""
    echo "All alerts completed! Check scripts_png_gen/output/ for generated files."
    echo "Alert reports: scripts_png_gen/output/*_report.json"
    echo "Alert charts: scripts_png_gen/output/*_alert.png"
fi
