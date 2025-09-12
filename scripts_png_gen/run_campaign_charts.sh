#!/bin/bash
# Campaign Performance Chart Generation Script
# Uses real data from ads.db instead of synthetic data

set -e

# Configuration
PROJECT_ROOT="/home/alex/dbt_ads/atlas"
ARGS_DIR="$PROJECT_ROOT/scripts_png_gen/input_args/campaign_data"
OUTPUT_DIR="$PROJECT_ROOT/scripts_png_gen/output"
DB_PATH="/home/alex/dbt_ads/atlas/z_GUI/ads.db"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    echo "Please ensure ads.db exists in the z_GUI directory"
    exit 1
fi

echo "=== Campaign Performance Chart Generation ==="
echo "Database: $DB_PATH"
echo "Args Directory: $ARGS_DIR"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Function to run a specific chart generation
run_chart() {
    local args_file="$1"
    local chart_name="$2"

    if [ ! -f "$args_file" ]; then
        echo "Warning: Args file not found: $args_file"
        return 1
    fi

    echo "Generating chart: $chart_name"
    echo "Args file: $args_file"

    # Run the CampaignGraphRunner with the args file
    cd "$PROJECT_ROOT"
    sbt "project atlas-eval" "runMain com.netflix.atlas.eval.tools.CampaignGraphRunner $(cat "$args_file")"

    if [ $? -eq 0 ]; then
        echo "✓ Successfully generated: $chart_name"
    else
        echo "✗ Failed to generate: $chart_name"
        return 1
    fi
    echo ""
}

# Generate campaign impression charts
echo "1. Campaign Impressions with Alert Threshold"
run_chart "$ARGS_DIR/campaign_impressions.args" "Campaign Impressions with Alert"

# You can add more chart types here
# echo "2. Campaign Clicks Analysis"
# run_chart "$ARGS_DIR/campaign_clicks.args" "Campaign Clicks Analysis"

# echo "3. Video Start Performance"
# run_chart "$ARGS_DIR/video_starts.args" "Video Start Performance"

echo "=== Chart Generation Complete ==="
echo "Output files:"
ls -la "$OUTPUT_DIR"/campaign_*.png 2>/dev/null || echo "No PNG files found"
ls -la "$OUTPUT_DIR"/campaign_*.json.gz 2>/dev/null || echo "No JSON files found"
