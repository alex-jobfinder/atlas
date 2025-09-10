#!/bin/bash
# Atlas Graph Style Templates Runner - Optimized Batch Version
# Usage: ./run_all_styles_optimized.sh [style_name]

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
    # Create a batch file for sbt - much faster than individual builds
    BATCH_FILE=$(mktemp)

    echo "project atlas-eval" >> "$BATCH_FILE"

    echo "Running all Atlas graph styles in optimized batch mode..."
    echo "This will be much faster than individual builds!"

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
    echo "All styles completed! Check target/manual/ for generated files."
fi
