"""
Comparison service for campaign analysis and comparison.
"""

import sqlite3
import os
from typing import Dict, Any, List, Optional


def compare_campaigns(campaign1_id: int, campaign2_id: int, metrics: List[str]) -> Dict[str, Any]:
    """
    Compare two campaigns side-by-side.

    Args:
        campaign1_id: First campaign ID
        campaign2_id: Second campaign ID
        metrics: List of metrics to compare

    Returns:
        Dictionary containing comparison data
    """
    if not os.path.exists("ads.db"):
        raise FileNotFoundError("Database not found")

    conn = sqlite3.connect("ads.db")
    cursor = conn.cursor()

    try:
        # Get both campaigns
        cursor.execute("SELECT id, name, objective, target_cpm, dsp_partner FROM campaigns WHERE id IN (?, ?)", (campaign1_id, campaign2_id))
        campaigns = cursor.fetchall()

        if len(campaigns) < 2:
            raise ValueError(f"One or both campaigns not found. Found: {len(campaigns)}")

        # Structure comparison
        result = {
            "campaign_1": {
                "id": campaigns[0][0],
                "name": campaigns[0][1],
                "objective": campaigns[0][2],
                "target_cpm": float(campaigns[0][3]) if campaigns[0][3] is not None else 0.0,
                "dsp_partner": campaigns[0][4]
            },
            "campaign_2": {
                "id": campaigns[1][0],
                "name": campaigns[1][1],
                "objective": campaigns[1][2],
                "target_cpm": float(campaigns[1][3]) if campaigns[1][3] is not None else 0.0,
                "dsp_partner": campaigns[1][4]
            },
            "comparison": {
                "cpm_difference": abs(float(campaigns[0][3] or 0) - float(campaigns[1][3] or 0)),
                "same_objective": campaigns[0][2] == campaigns[1][2],
                "same_dsp": campaigns[0][4] == campaigns[1][4]
            }
        }

        return result

    finally:
        conn.close()


def compare_by_objective(objective: str, top_n: int = 5) -> Dict[str, Any]:
    """
    Compare campaigns by objective type.

    Args:
        objective: Campaign objective to compare
        top_n: Number of top campaigns to show

    Returns:
        Dictionary containing comparison data
    """
    if not os.path.exists("ads.db"):
        raise FileNotFoundError("Database not found")

    conn = sqlite3.connect("ads.db")
    cursor = conn.cursor()

    try:
        # Get campaigns by objective
        cursor.execute("""
            SELECT id, name, target_cpm, status, dsp_partner
            FROM campaigns
            WHERE objective = ?
            ORDER BY target_cpm DESC
            LIMIT ?
        """, (objective, top_n))

        campaigns = cursor.fetchall()

        if not campaigns:
            return {
                "objective": objective,
                "total_campaigns": 0,
                "campaigns": [],
                "message": f"No campaigns found with objective: {objective}"
            }

        # Structure result
        result = {
            "objective": objective,
            "total_campaigns": len(campaigns),
            "campaigns": []
        }

        for row in campaigns:
            result["campaigns"].append({
                "id": row[0],
                "name": row[1],
                "target_cpm": row[2],
                "status": row[3],
                "dsp_partner": row[4]
            })

        return result

    finally:
        conn.close()
