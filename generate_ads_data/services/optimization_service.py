"""
Optimization service for campaign CPM and budget optimization.
"""

from typing import Dict, Any, Optional


def optimize_cpm(budget: float, objective: str, target_impressions: Optional[int] = None) -> Dict[str, Any]:
    """
    Find optimal CPM for your budget and objective.

    Args:
        budget: Total campaign budget
        objective: Campaign objective (AWARENESS, CONSIDERATION, CONVERSION)
        target_impressions: Optional target impression count

    Returns:
        Dictionary containing optimization results
    """
    # Basic CPM optimization based on objective
    if objective == "AWARENESS":
        suggested_cpm = budget / 1000  # Simple budget/1000 calculation
    elif objective == "CONSIDERATION":
        suggested_cpm = budget / 1500
    elif objective == "CONVERSION":
        suggested_cpm = budget / 2000
    else:
        suggested_cpm = budget / 1000  # Default to awareness

    # If target impressions provided, adjust CPM
    if target_impressions:
        suggested_cpm = budget / (target_impressions / 1000)

    # Determine budget efficiency
    if suggested_cpm < 20:
        budget_efficiency = "high"
    elif suggested_cpm < 50:
        budget_efficiency = "medium"
    else:
        budget_efficiency = "low"

    result = {
        "suggested_cpm": round(suggested_cpm, 2),
        "estimated_impressions": int(budget / suggested_cpm * 1000),
        "budget_efficiency": budget_efficiency,
        "objective": objective,
        "budget": budget
    }

    if target_impressions:
        result["target_impressions"] = target_impressions
        result["cpm_adjusted"] = True

    return result
