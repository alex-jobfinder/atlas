#!/bin/bash
# Atlas Visual Alert Runner - Shows alert rules visually on charts
# Usage: ./run_visual_alerts.sh [alert_name]

VISUAL_ALERTS_DIR="scripts/visual_alerts"
OUTPUT_DIR="target/manual"

if [ ! -d "$VISUAL_ALERTS_DIR" ]; then
    echo "Visual alerts directory not found: $VISUAL_ALERTS_DIR"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi

if [ -n "$1" ]; then
    # Run specific visual alert
    ALERT_FILE="$VISUAL_ALERTS_DIR/$1.args"
    if [ -f "$ALERT_FILE" ]; then
        echo "Running visual alert: $1"
        ARGS=$(cat "$ALERT_FILE")
        sbt "project atlas-eval" "runMain com.netflix.atlas.eval.tools.LocalAlertRunner $ARGS"
    else
        echo "Visual alert not found: $1"
        echo "Available visual alerts:"
        ls "$VISUAL_ALERTS_DIR"/*.args | sed "s|$VISUAL_ALERTS_DIR/||" | sed "s|\.args||"
    fi
else
    # Create a batch file for sbt - much faster than individual builds
    BATCH_FILE=$(mktemp)

    echo "project atlas-eval" >> "$BATCH_FILE"

    echo "Running all Atlas visual alert scenarios in optimized batch mode..."
    echo "This will show alert thresholds visually on charts!"

    for alert_file in "$VISUAL_ALERTS_DIR"/*.args; do
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
    echo "All visual alerts completed! Check target/manual/ for generated files."
    echo "Visual alert charts: target/manual/visual_*_alert.png"
    echo "Alert reports: target/manual/visual_*_alert_report.json"
fi
