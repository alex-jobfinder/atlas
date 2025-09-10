#!/bin/bash
# Atlas Graph Style Templates Runner
# Usage: ./run_all_styles.sh [style_name]

STYLES_DIR="scripts/styles"
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
    # Run all styles
    echo "Running all Atlas graph styles..."
    for style_file in "$STYLES_DIR"/*.args; do
        if [ -f "$style_file" ]; then
            style_name=$(basename "$style_file" .args)
            echo "Running style: $style_name"
            ARGS=$(cat "$style_file")
            sbt "project atlas-eval" "runMain com.netflix.atlas.eval.tools.LocalGraphRunner $ARGS"
            echo "Completed: $style_name"
            echo "---"
        fi
    done
    echo "All styles completed!"
fi
