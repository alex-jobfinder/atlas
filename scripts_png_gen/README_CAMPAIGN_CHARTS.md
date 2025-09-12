# Campaign Performance Chart Generation

This directory contains tools to generate Atlas charts using real campaign performance data from your `ads.db` SQLite database instead of synthetic data.

## Overview

The new process replaces the synthetic data generation in `LocalGraphRunner` with a custom database adapter that:
1. Connects to your SQLite `ads.db` database
2. Executes SQL queries to retrieve campaign performance data
3. Converts the data to Atlas TimeSeries format
4. Generates PNG charts with threshold alerts and visualizations

## Components

### 1. CampaignDatabase.scala
Custom database adapter that extends Atlas's `Database` interface to work with SQLite campaign data.

**Key Features:**
- Connects to SQLite database using JDBC
- Executes SQL queries for campaign performance data
- Converts SQL results to Atlas TimeSeries format
- Handles timestamp conversion (seconds to milliseconds)
- Creates properly tagged time series data

### 2. CampaignGraphRunner.scala
Modified version of `LocalGraphRunner` that uses real campaign data instead of synthetic presets.

**Usage:**
```bash
sbt "project atlas-eval" 'runMain com.netflix.atlas.eval.tools.CampaignGraphRunner \
  --db-path ads.db \
  --q "name,impressions,:eq,(,campaign_id,),:by,:sum,50e3,:2over,:gt,:vspan,40,:alpha,triggered,:legend,:rot,name,impressions,:eq,(,campaign_id,),:by,input,:legend,:rot,50e3,:const,threshold,:legend,:rot" \
  --s e-1w --e 2012-01-01T00:00 --tz UTC \
  --w 700 --h 300 --theme light \
  --out scripts_png_gen/output/campaign_impressions_with_alert.png'
```

### 3. campaign_data_converter.py
Python utility to help with data conversion and args file generation.

**Features:**
- Connects to SQLite database
- Retrieves campaign performance data
- Converts to Atlas TimeSeries format
- Generates Atlas StackLang queries
- Creates args files for CampaignGraphRunner

### 4. run_campaign_charts.sh
Shell script to automate chart generation using the new process.

## Data Format Requirements

### SQLite Database Schema
Your `ads.db` should have a `campaign_performance` table with these columns:
- `hour_ts`: DateTime with timezone
- `hour_unix_epoch`: Unix timestamp in seconds
- `impressions`: Integer count of ad impressions
- `clicks`: Integer count of clicks
- `video_start`: Integer count of video starts
- `campaign_id`: Integer campaign identifier

### Atlas TimeSeries Format
The data is converted to Atlas format with:
```json
{
  "tags": {
    "name": "impressions",
    "campaign_id": "1"
  },
  "label": "impressions,campaign_id=1",
  "data": {
    "startTime": 1640995200000,
    "step": 3600000,
    "values": [1000, 1200, 800, ...]
  }
}
```

## Usage Examples

### 1. Generate Campaign Impressions Chart
```bash
# Using the shell script
./scripts_png_gen/run_campaign_charts.sh

# Or manually
sbt "project atlas-eval" 'runMain com.netflix.atlas.eval.tools.CampaignGraphRunner $(cat scripts_png_gen/input_args/campaign_data/campaign_impressions.args)'
```

### 2. Convert Data and Generate Args File
```bash
# Convert data and create args file
python scripts_png_gen/campaign_data_converter.py \
  --db-path z_GUI/ads.db \
  --metric impressions \
  --threshold 50000 \
  --output-args scripts_png_gen/input_args/campaign_data/my_chart.args
```

### 3. Custom Chart Generation
```bash
# Generate chart with custom parameters
sbt "project atlas-eval" 'runMain com.netflix.atlas.eval.tools.CampaignGraphRunner \
  --db-path z_GUI/ads.db \
  --q "name,clicks,:eq,(,campaign_id,),:by,:sum,100,:2over,:gt,:vspan,40,:alpha,click_alerts,:legend,:rot,name,clicks,:eq,(,campaign_id,),:by,input,:legend,:rot,100,:const,threshold,:legend,:rot" \
  --s e-1w --e 2012-01-01T00:00 --tz UTC \
  --w 800 --h 400 --theme light \
  --out scripts_png_gen/output/campaign_clicks_analysis.png'
```

## Atlas StackLang Query Breakdown

The query `name,impressions,:eq,(,campaign_id,),:by,:sum,50e3,:2over,:gt,:vspan,40,:alpha,triggered,:legend,:rot` means:

1. `name,impressions,:eq` - Filter metrics where name=impressions
2. `(,campaign_id,),:by` - Group by campaign_id tag
3. `:sum` - Aggregate values using sum
4. `50e3,:2over,:gt` - Compare with threshold 50,000
5. `:vspan` - Create vertical span visualization
6. `40,:alpha` - Set 40% transparency
7. `triggered,:legend` - Label as "triggered"
8. `:rot` - Enable legend rotation

## Output Files

The process generates:
- **PNG Chart**: Visual representation with line charts and alert spans
- **V2 JSON**: Machine-readable chart definition with metadata
- **Logs**: Console output showing data retrieval and processing

## Troubleshooting

### Database Connection Issues
- Ensure `ads.db` exists in the specified path
- Check file permissions
- Verify SQLite driver is available (included in Atlas dependencies)

### Data Format Issues
- Verify `campaign_performance` table exists
- Check column names match expected schema
- Ensure `hour_unix_epoch` is in seconds (not milliseconds)

### Chart Generation Issues
- Check Atlas StackLang query syntax
- Verify time range parameters (`--s`, `--e`)
- Ensure output directory exists and is writable

## Integration with Existing Process

This new process is designed to be a drop-in replacement for the synthetic data generation. You can:

1. Use `CampaignGraphRunner` instead of `LocalGraphRunner`
2. Point to your real database instead of presets
3. Generate charts with actual campaign performance data
4. Apply the same Atlas StackLang expressions and visualizations

The output format remains the same, so existing chart processing tools will continue to work.
