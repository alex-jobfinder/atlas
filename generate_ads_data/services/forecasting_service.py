"""
Forecasting service for campaign ROI and performance predictions.
"""

from typing import Dict, Any, List


def project_roi(campaign_id: int, scenarios: int = 3, optimistic: bool = False) -> Dict[str, Any]:
    """
    Calculate ROI projections for a campaign.

    Args:
        campaign_id: Campaign ID to project ROI for
        scenarios: Number of scenarios to generate
        optimistic: Include optimistic scenario

    Returns:
        Dictionary containing ROI projections
    """
    # Basic ROI projections
    base_scenarios = [
        {"name": "Conservative", "roi": 1.5, "confidence": "high"},
        {"name": "Realistic", "roi": 2.5, "confidence": "medium"}
    ]

    if optimistic:
        base_scenarios.append({"name": "Optimistic", "roi": 4.0, "confidence": "low"})

    # Generate additional scenarios if requested
    if scenarios > len(base_scenarios):
        for i in range(scenarios - len(base_scenarios)):
            base_scenarios.append({
                "name": f"Scenario {i + 1}",
                "roi": round(1.0 + (i * 0.5), 1),
                "confidence": "medium"
            })

    result = {
        "campaign_id": campaign_id,
        "scenarios": base_scenarios[:scenarios],
        "total_scenarios": len(base_scenarios[:scenarios])
    }

    return result


def forecast_performance(campaign_id: int, days: int = 30, include_seasonal: bool = True) -> Dict[str, Any]:
    """
    Predict campaign performance over time.

    Args:
        campaign_id: Campaign ID to forecast
        days: Forecast period in days
        include_seasonal: Include seasonal adjustments

    Returns:
        Dictionary containing performance forecast
    """
    # Basic performance projections
    base_impressions = 10000
    base_clicks = 240
    base_conversions = 8
    base_spend = 1850

    # Apply seasonal adjustments if requested
    if include_seasonal:
        seasonal_multiplier = 1.2  # 20% boost for seasonal campaigns
        base_impressions = int(base_impressions * seasonal_multiplier)
        base_clicks = int(base_clicks * seasonal_multiplier)
        base_conversions = int(base_conversions * seasonal_multiplier)
        base_spend = int(base_spend * seasonal_multiplier)

    result = {
        "campaign_id": campaign_id,
        "forecast_days": days,
        "projected_metrics": {
            "impressions": days * base_impressions,
            "clicks": days * base_clicks,
            "conversions": days * base_conversions,
            "spend": days * base_spend
        },
        "confidence_level": "medium",
        "seasonal_adjustments": include_seasonal
    }

    return result
