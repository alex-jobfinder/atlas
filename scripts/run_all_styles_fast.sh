#!/bin/bash
# Atlas Graph Style Templates Runner - Optimized Single Build Version
# Usage: ./run_all_styles_fast.sh [style_name]

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
    # Run all styles using sbt batch mode - much faster!
    echo "Running all Atlas graph styles in optimized batch mode..."

    # Create sbt commands for all styles
    SBT_COMMANDS=""
    for style_file in "$STYLES_DIR"/*.args; do
        if [ -f "$style_file" ]; then
            style_name=$(basename "$style_file" .args)
            ARGS=$(cat "$style_file")
            SBT_COMMANDS="${SBT_COMMANDS}runMain com.netflix.atlas.eval.tools.LocalGraphRunner $ARGS;"
        fi
    done

    # Run all commands in one sbt session using batch mode
    echo "Executing all styles..."
    sbt "project atlas-eval" "$SBT_COMMANDS"

    echo "All styles completed!"
fi
