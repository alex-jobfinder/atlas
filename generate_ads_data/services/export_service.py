"""
Export service for campaign data in various formats.
"""

import sqlite3
import os
from typing import Dict, Any, Optional


def export_campaign(campaign_id: int, format: str, include_performance: bool = True) -> Dict[str, Any]:
    """
    Export campaign data in specified format.

    Args:
        campaign_id: ID of campaign to export
        format: Export format (json, csv, excel)
        include_performance: Whether to include performance data

    Returns:
        Dictionary containing export data
    """
    if not os.path.exists("ads.db"):
        raise FileNotFoundError("Database not found")

    conn = sqlite3.connect("ads.db")
    cursor = conn.cursor()

    try:
        # Get campaign data
        cursor.execute("""
            SELECT c.*, a.name as advertiser_name, a.brand
            FROM campaigns c
            JOIN advertisers a ON c.advertiser_id = a.id
            WHERE c.id = ?
        """, (campaign_id,))

        campaign = cursor.fetchone()
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")

        # Get line items
        cursor.execute("SELECT * FROM line_items WHERE campaign_id = ?", (campaign_id,))
        line_items = cursor.fetchall()

        # Get creatives through line items
        if line_items:
            line_item_ids = [str(item[0]) for item in line_items]
            placeholders = ','.join(['?' for _ in line_item_ids])
            cursor.execute(f"SELECT * FROM creatives WHERE line_item_id IN ({placeholders})", line_item_ids)
            creatives = cursor.fetchall()
        else:
            creatives = []

        # Get performance data if requested
        performance = []
        if include_performance:
            cursor.execute("SELECT * FROM campaign_performance WHERE campaign_id = ? LIMIT 100", (campaign_id,))
            performance = cursor.fetchall()

        # Structure the data
        result = {
            "campaign_id": campaign_id,
            "campaign_data": {
                "name": campaign[1],
                "status": campaign[2],
                "created_at": campaign[3],
                "updated_at": campaign[4],
                "objective": campaign[6],
                "currency": campaign[7],
                "target_cpm": campaign[8],
                "dsp_partner": campaign[9],
                "advertiser": campaign[-2],
                "brand": campaign[-1]
            },
            "line_items_count": len(line_items),
            "creatives_count": len(creatives),
            "performance_records": len(performance) if include_performance else 0
        }

        # Handle different formats
        if format == "csv":
            import csv
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Field", "Value"])
            for key, value in result.items():
                if isinstance(value, dict):
                    for k, v in value.items():
                        writer.writerow([f"{key}.{k}", v])
                else:
                    writer.writerow([key, value])
            return {"csv_data": output.getvalue(), "format": "csv"}
        elif format == "excel":
            # Excel export would require additional libraries
            return {"error": "Excel export not available", "format": "excel"}
        else:
            # Default to JSON
            return result

    finally:
        conn.close()
