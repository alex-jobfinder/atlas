#!/usr/bin/env python3
"""
Campaign Data Converter
Utility to convert SQLite campaign performance data to Atlas-compatible format
"""

import sqlite3
import pandas as pd
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any

class CampaignDataConverter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None

    def connect(self):
        """Connect to the SQLite database."""
        self.connection = sqlite3.connect(self.db_path)
        return self.connection

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()

    def get_campaign_data(self, campaign_id: int = 1, days_back: int = 14) -> pd.DataFrame:
        """
        Retrieve campaign performance data for the specified period.

        Args:
            campaign_id: Campaign ID to query
            days_back: Number of days back to retrieve data

        Returns:
            DataFrame with campaign performance data
        """
        if not self.connection:
            self.connect()

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        query = """
        SELECT
            hour_ts,
            hour_unix_epoch,
            impressions,
            clicks,
            video_start,
            frequency,
            reach,
            spend
        FROM campaign_performance
        WHERE campaign_id = ?
        AND hour_unix_epoch >= ?
        AND hour_unix_epoch <= ?
        ORDER BY hour_unix_epoch ASC
        """

        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())

        df = pd.read_sql_query(
            query,
            self.connection,
            params=(campaign_id, start_timestamp, end_timestamp)
        )

        return df

    def convert_to_atlas_timeseries(self, df: pd.DataFrame, metric: str = "impressions") -> Dict[str, Any]:
        """
        Convert DataFrame to Atlas TimeSeries format.

        Args:
            df: DataFrame with campaign data
            metric: Metric to extract (impressions, clicks, video_start, etc.)

        Returns:
            Dictionary in Atlas TimeSeries format
        """
        if df.empty:
            return {}

        # Convert timestamps to milliseconds
        timestamps_ms = df['hour_unix_epoch'] * 1000

        # Extract values for the specified metric
        if metric not in df.columns:
            raise ValueError(f"Metric '{metric}' not found in data. Available: {list(df.columns)}")

        values = df[metric].tolist()

        # Calculate step size (assuming hourly data)
        step_size = 3600000  # 1 hour in milliseconds

        # Create Atlas TimeSeries format
        atlas_data = {
            "tags": {
                "name": metric,
                "campaign_id": "1"
            },
            "label": f"{metric},campaign_id=1",
            "data": {
                "startTime": timestamps_ms.iloc[0] if len(timestamps_ms) > 0 else 0,
                "step": step_size,
                "values": values
            }
        }

        return atlas_data

    def generate_atlas_query(self, metric: str = "impressions", threshold: float = 50000) -> str:
        """
        Generate Atlas StackLang query for campaign data with threshold alerts.

        Args:
            metric: Metric to query (impressions, clicks, video_start, etc.)
            threshold: Threshold value for alert visualization

        Returns:
            Atlas StackLang query string
        """
        query = f"""
        name,{metric},:eq,(,campaign_id,),:by,:sum,{threshold:g},:2over,:gt,:vspan,40,:alpha,triggered,:legend,:rot,
        name,{metric},:eq,(,campaign_id,),:by,input,:legend,:rot,
        {threshold:g},:const,threshold,:legend,:rot
        """.strip().replace('\n', '')

        return query

    def create_args_file(self, output_path: str, metric: str = "impressions", threshold: float = 50000):
        """
        Create an args file for CampaignGraphRunner.

        Args:
            output_path: Path to save the args file
            metric: Metric to visualize
            threshold: Threshold value for alerts
        """
        atlas_query = self.generate_atlas_query(metric, threshold)

        args_content = f"""--db-path ads.db --q "{atlas_query}" --s e-1w --e 2012-01-01T00:00 --tz UTC --theme light --w 700 --h 300 --out scripts_png_gen/output/campaign_{metric}_with_alert.png --emit-v2 scripts_png_gen/output/campaign_{metric}_with_alert.v2.json.gz"""

        with open(output_path, 'w') as f:
            f.write(args_content)

        print(f"Created args file: {output_path}")
        print(f"Query: {atlas_query}")

def main():
    parser = argparse.ArgumentParser(description="Convert campaign data to Atlas format")
    parser.add_argument("--db-path", default="ads.db", help="Path to SQLite database")
    parser.add_argument("--campaign-id", type=int, default=1, help="Campaign ID to query")
    parser.add_argument("--days-back", type=int, default=14, help="Number of days back to retrieve")
    parser.add_argument("--metric", default="impressions", help="Metric to analyze")
    parser.add_argument("--threshold", type=float, default=50000, help="Threshold value for alerts")
    parser.add_argument("--output-args", help="Output args file path")
    parser.add_argument("--output-json", help="Output Atlas JSON file path")

    args = parser.parse_args()

    converter = CampaignDataConverter(args.db_path)

    try:
        # Get campaign data
        print(f"Retrieving campaign {args.campaign_id} data for last {args.days_back} days...")
        df = converter.get_campaign_data(args.campaign_id, args.days_back)

        if df.empty:
            print("No data found for the specified criteria.")
            return

        print(f"Retrieved {len(df)} data points")
        print(f"Date range: {df['hour_ts'].min()} to {df['hour_ts'].max()}")
        print(f"Available metrics: {list(df.columns)}")

        # Convert to Atlas format
        atlas_data = converter.convert_to_atlas_timeseries(df, args.metric)

        if atlas_data:
            print(f"Converted {args.metric} data to Atlas format")
            print(f"Data points: {len(atlas_data['data']['values'])}")
            print(f"Time range: {atlas_data['data']['startTime']} to {atlas_data['data']['startTime'] + (len(atlas_data['data']['values']) - 1) * atlas_data['data']['step']}")

        # Output Atlas JSON if requested
        if args.output_json:
            with open(args.output_json, 'w') as f:
                json.dump(atlas_data, f, indent=2)
            print(f"Saved Atlas JSON to: {args.output_json}")

        # Create args file if requested
        if args.output_args:
            converter.create_args_file(args.output_args, args.metric, args.threshold)

    finally:
        converter.close()

if __name__ == "__main__":
    main()
