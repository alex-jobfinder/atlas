#!/bin/bash
# !scripts/get_schema_cached.sh
SCHEMA_FILE="dbt_ads_project/xml_schema/dbt_db_schema.xml"
MAX_AGE_HOURS=24

# Check if schema file exists and is less than 24 hours old
if [ -f "$SCHEMA_FILE" ]; then
    # Get file modification time in seconds since epoch
    FILE_TIME=$(stat -c %Y "$SCHEMA_FILE")
    CURRENT_TIME=$(date +%s)
    AGE_HOURS=$(( (CURRENT_TIME - FILE_TIME) / 3600 ))

    if [ $AGE_HOURS -lt $MAX_AGE_HOURS ]; then
        echo "Using cached schema (age: ${AGE_HOURS}h)"
        exit 0
    fi
fi

echo "Generating fresh schema..."
uv run python dbt_ads_project/query_get_schema.py
