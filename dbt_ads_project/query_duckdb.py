#!/usr/bin/env python3
"""
DuckDB Query Script for Campaign Performance Analysis
Run with: python query_duckdb.py
"""

import duckdb
import pandas as pd
from datetime import datetime

def connect_to_db():
    """Connect to the DuckDB database"""
    return duckdb.connect('dbt.duckdb')

def explore_database(conn):
    """Explore what's in the database"""
    print("🔍 Exploring Database Structure")
    print("=" * 50)

    # List all tables
    tables = conn.execute("SHOW TABLES").fetchall()
    print(f"Tables found: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")

    print("\n📊 Table Details:")
    for table in tables:
        table_name = table[0]
        print(f"\n{table_name}:")
        schema = conn.execute(f"DESCRIBE {table_name}").fetchall()
        for col in schema:
            print(f"  {col[0]}: {col[1]}")

def analyze_campaign_performance(conn):
    """Analyze campaign performance data"""
    print("\n🎯 Campaign Performance Analysis")
    print("=" * 50)

    # Basic counts
    total_rows = conn.execute("SELECT COUNT(*) FROM campaign_performance").fetchone()[0]
    print(f"Total rows: {total_rows:,}")

    # Campaign overview with calculated CTR
    campaigns = conn.execute("""
        SELECT
            campaign_id,
            COUNT(*) as hourly_records,
            SUM(impressions) as total_impressions,
            SUM(clicks) as total_clicks,
            SUM(spend) as total_spend,
            CASE
                WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS FLOAT) / SUM(impressions), 4)
                ELSE 0
            END as avg_ctr
        FROM campaign_performance
        GROUP BY campaign_id
        ORDER BY total_impressions DESC
    """).fetchall()

    print(f"\nCampaigns found: {len(campaigns)}")
    for campaign in campaigns:
        campaign_id, records, impressions, clicks, spend, ctr = campaign
        print(f"  Campaign {campaign_id}: {impressions:,} impressions, {clicks:,} clicks, ${spend:,} spend, {ctr:.4f} CTR")

    # Time analysis with calculated CTR
    print("\n⏰ Time-based Analysis:")
    time_stats = conn.execute("""
        SELECT
            hour_of_day,
            COUNT(*) as records,
            AVG(impressions) as avg_impressions,
            CASE
                WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS FLOAT) / SUM(impressions), 4)
                ELSE 0
            END as avg_ctr
        FROM campaign_performance
        GROUP BY hour_of_day
        ORDER BY hour_of_day
    """).fetchall()

    for hour, records, avg_imp, avg_ctr in time_stats:
        print(f"  Hour {hour:2d}: {records:3d} records, {avg_imp:6.0f} avg impressions, {avg_ctr:.4f} avg CTR")

    # Business hours vs non-business hours with calculated CTR
    business_stats = conn.execute("""
        SELECT
            is_business_hour,
            COUNT(*) as records,
            AVG(impressions) as avg_impressions,
            CASE
                WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS FLOAT) / SUM(impressions), 4)
                ELSE 0
            END as avg_ctr,
            SUM(spend) as total_spend
        FROM campaign_performance
        GROUP BY is_business_hour
    """).fetchall()

    print("\n🏢 Business Hours Analysis:")
    for is_business, records, avg_imp, avg_ctr, total_spend in business_stats:
        period = "Business Hours" if is_business else "Non-Business Hours"
        print(f"  {period}: {records:3d} records, {avg_imp:6.0f} avg impressions, {avg_ctr:.4f} avg CTR, ${total_spend:,} spend")

def query_specific_metrics(conn):
    """Query specific metrics and KPIs"""
    print("\n📈 Key Performance Metrics")
    print("=" * 50)

    # Overall performance with calculated CTR
    overall = conn.execute("""
        SELECT
            SUM(impressions) as total_impressions,
            SUM(clicks) as total_clicks,
            SUM(spend) as total_spend,
            CASE
                WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS FLOAT) / SUM(impressions), 4)
                ELSE 0
            END as overall_ctr,
            SUM(viewable_impressions) as total_viewable,
            SUM(video_q100) as total_video_completions
        FROM campaign_performance
    """).fetchone()

    print(f"Total Impressions: {overall[0]:,}")
    print(f"Total Clicks: {overall[1]:,}")
    print(f"Total Spend: ${overall[2]:,}")
    print(f"Overall CTR: {overall[3]:.4f}")
    print(f"Viewable Impressions: {overall[4]:,}")
    print(f"Video Completions: {overall[5]:,}")

    # Calculate derived metrics
    if overall[0] > 0:
        cpm = (overall[2] / overall[0]) * 1000
        cpc = overall[2] / overall[1] if overall[1] > 0 else 0
        viewability_rate = overall[4] / overall[0] if overall[0] > 0 else 0
        video_completion_rate = overall[5] / overall[0] if overall[0] > 0 else 0

        print(f"\n📊 Derived Metrics:")
        print(f"CPM: ${cpm:.2f}")
        print(f"CPC: ${cpc:.2f}")
        print(f"Viewability Rate: {viewability_rate:.2%}")
        print(f"Video Completion Rate: {video_completion_rate:.2%}")

def analyze_audience_data(conn):
    """Analyze audience_json data if available"""
    print("\n👥 Audience Data Analysis")
    print("=" * 50)

    try:
        # Check if audience_json column exists and has data
        sample_audience = conn.execute("""
            SELECT audience_json
            FROM campaign_performance
            WHERE audience_json IS NOT NULL
            AND audience_json != ''
            LIMIT 1
        """).fetchone()

        if sample_audience and sample_audience[0]:
            print("✅ Audience JSON data found")

            # Count records with audience data
            audience_count = conn.execute("""
                SELECT COUNT(*)
                FROM campaign_performance
                WHERE audience_json IS NOT NULL
                AND audience_json != ''
            """).fetchone()[0]

            print(f"Records with audience data: {audience_count:,}")

            # Sample audience breakdown
            print("\n📋 Sample audience data structure:")
            print(sample_audience[0][:200] + "..." if len(sample_audience[0]) > 200 else sample_audience[0])

        else:
            print("⚠️  No audience JSON data found")

    except Exception as e:
        print(f"⚠️  Could not analyze audience data: {e}")

def export_to_csv(conn):
    """Export data to CSV for external analysis"""
    print("\n💾 Exporting Data to CSV")
    print("=" * 50)

    # Export campaign summary with calculated CTR
    campaign_summary = conn.execute("""
        SELECT
            campaign_id,
            COUNT(*) as hourly_records,
            SUM(impressions) as total_impressions,
            SUM(clicks) as total_clicks,
            SUM(spend) as total_spend,
            CASE
                WHEN SUM(impressions) > 0 THEN ROUND(CAST(SUM(clicks) AS FLOAT) / SUM(impressions), 4)
                ELSE 0
            END as avg_ctr,
            SUM(viewable_impressions) as total_viewable,
            SUM(video_q100) as total_video_completions
        FROM campaign_performance
        GROUP BY campaign_id
        ORDER BY total_impressions DESC
    """).fetchdf()

    # campaign_summary.to_csv('campaign_summary.csv', index=False)
    print(f"Campaign summary exported to campaign_summary.csv ({len(campaign_summary)} campaigns)")

    # Export hourly performance with calculated CTR
    hourly_performance = conn.execute("""
        SELECT
            hour_ts,
            hour_of_day,
            day_of_week,
            is_business_hour,
            campaign_id,
            impressions,
            clicks,
            CASE
                WHEN impressions > 0 THEN ROUND(CAST(clicks AS FLOAT) / impressions, 4)
                ELSE 0
            END as ctr,
            spend,
            viewable_impressions,
            video_q100
        FROM campaign_performance
        ORDER BY hour_ts
    """).fetchdf()

    # hourly_performance.to_csv('hourly_performance.csv', index=False)
    print(f"Hourly performance exported to hourly_performance.csv ({len(hourly_performance)} records)")

def main():
    """Main function to run all analyses"""
    print("🚀 DuckDB Campaign Performance Analysis")
    print("=" * 60)

    try:
        conn = connect_to_db()

        # Run analyses
        explore_database(conn)
        analyze_campaign_performance(conn)
        query_specific_metrics(conn)
        analyze_audience_data(conn)
        export_to_csv(conn)

        print("\n✅ Analysis complete! Check the generated CSV files.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
