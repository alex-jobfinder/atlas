"""
Campaign service for listing and managing campaigns.
"""

import sqlite3
import os
from typing import List, Dict, Optional


def list_campaigns(objective: Optional[str] = None, status: Optional[str] = None) -> List[Dict]:
    """
    List campaigns with optional filtering.

    Args:
        objective: Filter by campaign objective
        status: Filter by campaign status

    Returns:
        List of campaign dictionaries
    """
    if not os.path.exists("ads.db"):
        return []

    conn = sqlite3.connect("ads.db")
    cursor = conn.cursor()

    try:
        # Build query with optional filters
        query = "SELECT id, name, objective, status, target_cpm, dsp_partner FROM campaigns"
        params = []

        if objective or status:
            query += " WHERE"
            if objective:
                query += " objective = ?"
                params.append(objective)
            if status:
                if objective:
                    query += " AND"
                query += " status = ?"
                params.append(status)

        cursor.execute(query, params)
        campaigns = cursor.fetchall()

        result = []
        for row in campaigns:
            result.append({
                "id": row[0],
                "name": row[1],
                "objective": row[2],
                "status": row[3],
                "target_cpm": row[4],
                "dsp_partner": row[5]
            })

        return result

    finally:
        conn.close()
