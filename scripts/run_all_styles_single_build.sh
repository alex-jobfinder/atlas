#!/bin/bash
# Atlas Graph Style Templates Runner - Single Build Version
# Usage: ./run_all_styles_single_build.sh [style_name]

STYLES_DIR="scripts/styles"
OUTPUT_DIR="target/manual"

if [ ! -d "$STYLES_DIR" ]; then
    echo "Styles directory not found: $STYLES_DIR"
    exit 1
fi

if [ ! -d "$OUTPUT_DIR" ]; then
    mkdir -p "$OUTPUT_DIR"
fi

# Build the project once
echo "Building Atlas project..."
sbt "project atlas-eval" compile

if [ $? -ne 0 ]; then
    echo "Build failed!"
    exit 1
fi

echo "Build completed successfully!"
echo ""

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
    # Run all styles in one sbt session
    echo "Running all Atlas graph styles in single build session..."
    
    # Create a temporary script with all the runMain commands
    TEMP_SCRIPT=$(mktemp)
    echo "project atlas-eval" > "$TEMP_SCRIPT"
    
    for style_file in "$STYLES_DIR"/*.args; do
        if [ -f "$style_file" ]; then
            style_name=$(basename "$style_file" .args)
            echo "echo \"Running style: $style_name\"" >> "$TEMP_SCRIPT"
            ARGS=$(cat "$style_file")
            echo "runMain com.netflix.atlas.eval.tools.LocalGraphRunner $ARGS" >> "$TEMP_SCRIPT"
            echo "echo \"Completed: $style_name\"" >> "$TEMP_SCRIPT"
            echo "echo \"---\"" >> "$TEMP_SCRIPT"
        fi
    done
    
    # Run all commands in one sbt session
    sbt < "$TEMP_SCRIPT"
    
    # Clean up
    rm "$TEMP_SCRIPT"
    
    echo "All styles completed!"
fi
