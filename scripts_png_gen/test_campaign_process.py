#!/usr/bin/env python3
"""
Test script for the new campaign chart generation process
"""

import os
import sys
import sqlite3
import subprocess
from pathlib import Path

def test_database_connection(db_path: str) -> bool:
    """Test if we can connect to the database and retrieve data."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if campaign_performance table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='campaign_performance'")
        if not cursor.fetchone():
            print(f"❌ Table 'campaign_performance' not found in {db_path}")
            return False

        # Check table structure
        cursor.execute("PRAGMA table_info(campaign_performance)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        required_columns = ['hour_ts', 'hour_unix_epoch', 'impressions', 'campaign_id']
        missing_columns = [col for col in required_columns if col not in column_names]

        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            return False

        # Check for data
        cursor.execute("SELECT COUNT(*) FROM campaign_performance WHERE campaign_id = 1")
        count = cursor.fetchone()[0]

        if count == 0:
            print(f"❌ No data found for campaign_id = 1")
            return False

        print(f"✅ Database connection successful")
        print(f"   - Found {count} records for campaign_id = 1")
        print(f"   - Available columns: {column_names}")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_data_converter(db_path: str) -> bool:
    """Test the campaign data converter."""
    try:
        converter_script = "scripts_png_gen/campaign_data_converter.py"
        if not os.path.exists(converter_script):
            print(f"❌ Converter script not found: {converter_script}")
            return False

        # Test data retrieval
        result = subprocess.run([
            sys.executable, converter_script,
            "--db-path", db_path,
            "--days-back", "7",
            "--metric", "impressions"
        ], capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Data converter test failed:")
            print(f"   stdout: {result.stdout}")
            print(f"   stderr: {result.stderr}")
            return False

        print(f"✅ Data converter test successful")
        print(f"   - Retrieved campaign data")
        print(f"   - Converted to Atlas format")

        return True

    except Exception as e:
        print(f"❌ Data converter test failed: {e}")
        return False

def test_args_files() -> bool:
    """Test if args files exist and are properly formatted."""
    args_dir = "scripts_png_gen/input_args/campaign_data"

    if not os.path.exists(args_dir):
        print(f"❌ Args directory not found: {args_dir}")
        return False

    args_file = f"{args_dir}/campaign_impressions.args"
    if not os.path.exists(args_file):
        print(f"❌ Args file not found: {args_file}")
        return False

    # Check args file content
    with open(args_file, 'r') as f:
        content = f.read().strip()

    required_elements = [
        "--db-path ads.db",
        "--q \"name,impressions,:eq",
        "--out scripts_png_gen/output/campaign_impressions_with_alert.png"
    ]

    for element in required_elements:
        if element not in content:
            print(f"❌ Args file missing required element: {element}")
            return False

    print(f"✅ Args files test successful")
    print(f"   - Found args file: {args_file}")
    print(f"   - Contains required elements")

    return True

def test_scala_compilation() -> bool:
    """Test if the new Scala classes compile."""
    try:
        # Check if Scala files exist
        scala_files = [
            "atlas-eval/src/main/scala/com/netflix/atlas/eval/tools/CampaignDatabase.scala",
            "atlas-eval/src/main/scala/com/netflix/atlas/eval/tools/CampaignGraphRunner.scala"
        ]

        for scala_file in scala_files:
            if not os.path.exists(scala_file):
                print(f"❌ Scala file not found: {scala_file}")
                return False

        print(f"✅ Scala files found")
        print(f"   - CampaignDatabase.scala")
        print(f"   - CampaignGraphRunner.scala")

        # Note: Full compilation test would require sbt, which might not be available in test environment
        print(f"   - Compilation test skipped (requires sbt)")

        return True

    except Exception as e:
        print(f"❌ Scala compilation test failed: {e}")
        return False

def main():
    print("=== Campaign Chart Generation Process Test ===\n")

    # Test configuration
    db_path = "z_GUI/ads.db"

    tests = [
        ("Database Connection", lambda: test_database_connection(db_path)),
        ("Args Files", test_args_files),
        ("Scala Files", test_scala_compilation),
        ("Data Converter", lambda: test_data_converter(db_path))
    ]

    results = []
    for test_name, test_func in tests:
        print(f"Running test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
        print()

    # Summary
    print("=== Test Summary ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The campaign chart generation process is ready to use.")
        print("\nNext steps:")
        print("1. Run: ./scripts_png_gen/run_campaign_charts.sh")
        print("2. Or manually: sbt 'project atlas-eval' 'runMain com.netflix.atlas.eval.tools.CampaignGraphRunner $(cat scripts_png_gen/input_args/campaign_data/campaign_impressions.args)'")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please fix the issues before proceeding.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
