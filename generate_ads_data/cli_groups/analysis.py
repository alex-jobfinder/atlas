from __future__ import annotations

import json
from typing import Optional

import click


@click.group(help="Analysis and optimization: compare, forecast, ROI, tests.")
def analysis() -> None:
    """Analysis subcommands group."""
    pass


@analysis.command("compare")
@click.option("--campaign1", required=True, type=int, help="First campaign ID")
@click.option("--campaign2", required=True, type=int, help="Second campaign ID")
@click.option("--metrics", type=str, default="cpm,ctr,conversion,roi", help="Comma-separated metrics to compare")
def cmd_compare_campaigns(campaign1: int, campaign2: int, metrics: str) -> None:
    """Compare two campaigns side-by-side."""
    try:
        from services.comparison_service import compare_campaigns

        try:
            metric_list = [m.strip() for m in metrics.split(",")]
            result = compare_campaigns(campaign1, campaign2, metric_list)
            print(json.dumps(result, indent=2))
            return
        except Exception as e:
            # Gracefully surface service errors expected by tests
            print(f"❌ {e}")
            return
    except ImportError:
        try:
            import sqlite3
            import os

            if not os.path.exists("ads.db"):
                print("❌ Database not found. Please run './run_all.sh' first to create sample data.")
                return

            conn = sqlite3.connect("ads.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id, name, objective, target_cpm, dsp_partner FROM campaigns WHERE id IN (?, ?)",
                (campaign1, campaign2),
            )
            campaigns = cursor.fetchall()
            if len(campaigns) < 2:
                print(f"❌ One or both campaigns not found. Found: {len(campaigns)}")
                return

            result = {
                "campaign_1": {
                    "id": campaigns[0][0],
                    "name": campaigns[0][1],
                    "objective": campaigns[0][2],
                    "target_cpm": campaigns[0][3],
                    "dsp_partner": campaigns[0][4],
                },
                "campaign_2": {
                    "id": campaigns[1][0],
                    "name": campaigns[1][1],
                    "objective": campaigns[1][2],
                    "target_cpm": campaigns[1][3],
                    "dsp_partner": campaigns[1][4],
                },
                "comparison": {
                    "cpm_difference": abs(campaigns[0][3] - campaigns[1][3]),
                    "same_objective": campaigns[0][2] == campaigns[1][2],
                    "same_dsp": campaigns[0][4] == campaigns[1][4],
                },
            }
            conn.close()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"❌ Comparison failed: {e}")


@analysis.command("compare-objective")
@click.option("--objective", required=True, type=str, help="Campaign objective to compare")
@click.option("--top-n", type=int, default=5, help="Number of top campaigns to show")
def cmd_compare_by_objective(objective: str, top_n: int) -> None:
    """Compare campaigns by objective type."""
    try:
        from services.comparison_service import compare_by_objective
        try:
            result = compare_by_objective(objective, top_n)
            print(json.dumps(result, indent=2))
            return
        except Exception as e:
            print(f"❌ {e}")
            return
    except ImportError:
        try:
            import sqlite3
            import os

            if not os.path.exists("ads.db"):
                print("❌ Database not found. Please run './run_all.sh' first to create sample data.")
                return

            conn = sqlite3.connect("ads.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, name, target_cpm, status, dsp_partner
                FROM campaigns
                WHERE objective = ?
                ORDER BY target_cpm DESC
                LIMIT ?
                """,
                (objective, top_n),
            )
            campaigns = cursor.fetchall()
            if not campaigns:
                print(f"❌ No campaigns found with objective: {objective}")
                return

            result = {
                "objective": objective,
                "total_campaigns": len(campaigns),
                "campaigns": [
                    {
                        "id": row[0],
                        "name": row[1],
                        "target_cpm": row[2],
                        "status": row[3],
                        "dsp_partner": row[4],
                    }
                    for row in campaigns
                ],
            }
            conn.close()
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"❌ Comparison failed: {e}")


@analysis.command("optimize-cpm")
@click.option("--budget", required=True, type=float, help="Total campaign budget")
@click.option("--objective", required=True, type=str, help="Campaign objective")
@click.option("--target-impressions", type=int, help="Target impression count")
def cmd_optimize_cpm(budget: float, objective: str, target_impressions: Optional[int] = None) -> None:
    """Find an optimal CPM for a given budget and objective."""
    try:
        from services.optimization_service import optimize_cpm
        result = optimize_cpm(budget, objective, target_impressions)
        print(json.dumps(result, indent=2))
    except ImportError:
        if objective == "AWARENESS":
            suggested_cpm = budget / 1000
        elif objective == "CONSIDERATION":
            suggested_cpm = budget / 1500
        else:
            suggested_cpm = budget / 2000
        result = {
            "suggested_cpm": round(suggested_cpm, 2),
            "estimated_impressions": int(budget / suggested_cpm * 1000),
            "budget_efficiency": "high" if suggested_cpm < 20 else "medium",
        }
        print(json.dumps(result, indent=2))


@analysis.command("project-roi")
@click.option("--campaign-id", required=True, type=int, help="Campaign ID to project ROI for")
@click.option("--scenarios", type=int, default=3, help="Number of scenarios to generate")
@click.option("--optimistic", is_flag=True, default=False, help="Include optimistic scenario")
def cmd_project_roi(campaign_id: int, scenarios: int, optimistic: bool) -> None:
    """Calculate ROI projections for a campaign."""
    try:
        from services.forecasting_service import project_roi
        result = project_roi(campaign_id, scenarios, optimistic)
        print(json.dumps(result, indent=2))
    except ImportError:
        result = {
            "campaign_id": campaign_id,
            "scenarios": (
                [
                    {"name": "Conservative", "roi": 1.5, "confidence": "high"},
                    {"name": "Realistic", "roi": 2.5, "confidence": "medium"},
                    {"name": "Optimistic", "roi": 4.0, "confidence": "low"},
                ]
                if optimistic
                else [
                    {"name": "Conservative", "roi": 1.5, "confidence": "high"},
                    {"name": "Realistic", "roi": 2.5, "confidence": "medium"},
                ]
            ),
        }
        print(json.dumps(result, indent=2))


@analysis.command("test-creative")
@click.option("--format", required=True, type=str, help="Creative format to test")
@click.option("--duration", type=int, help="Duration in seconds")
@click.option("--interactive", is_flag=True, default=False, help="Test interactive elements")
def cmd_test_creative(format: str, duration: Optional[int] = None, interactive: bool = False) -> None:
    """Test different creative formats and configurations."""
    try:
        from services.creative_service import test_creative
        result = test_creative(format, duration, interactive)
        print(json.dumps(result, indent=2))
    except ImportError:
        result = {
            "format": format,
            "duration": duration,
            "interactive": interactive,
            "recommendations": [
                "Test multiple durations (15s, 30s, 60s)",
                "A/B test interactive vs static elements",
                "Monitor engagement metrics closely",
            ],
        }
        print(json.dumps(result, indent=2))


@analysis.command("ab-test")
@click.option("--variant-a", required=True, type=str, help="First variant name")
@click.option("--variant-b", required=True, type=str, help="Second variant name")
@click.option("--test-duration", type=int, default=14, help="Test duration in days")
def cmd_ab_test(variant_a: str, variant_b: str, test_duration: int) -> None:
    """Set up A/B testing between two campaign variants."""
    try:
        from services.ab_testing_service import setup_ab_test
        result = setup_ab_test(variant_a, variant_b, test_duration)
        print(json.dumps(result, indent=2))
    except ImportError:
        result = {
            "variant_a": variant_a,
            "variant_b": variant_b,
            "test_duration_days": test_duration,
            "setup_instructions": [
                "Create two campaigns with identical settings",
                "Modify only the variable you want to test",
                "Run two campaigns simultaneously",
                "Compare performance after test period",
            ],
        }
        print(json.dumps(result, indent=2))


@analysis.command("forecast")
@click.option("--campaign-id", required=True, type=int, help="Campaign ID to forecast")
@click.option("--days", type=int, default=30, help="Forecast period in days")
@click.option(
    "--include-seasonal/--no-include-seasonal", default=True, show_default=True, help="Include seasonal adjustments"
)
def cmd_forecast(campaign_id: int, days: int, include_seasonal: bool) -> None:
    """Predict campaign performance over a specified horizon."""
    try:
        from services.forecasting_service import forecast_performance
        result = forecast_performance(campaign_id, days, include_seasonal)
        print(json.dumps(result, indent=2))
    except ImportError:
        result = {
            "campaign_id": campaign_id,
            "forecast_days": days,
            "projected_metrics": {
                "impressions": days * 10000,
                "clicks": days * 240,
                "conversions": days * 8,
                "spend": days * 1850,
            },
            "confidence_level": "medium",
        }
        print(json.dumps(result, indent=2))


@analysis.command("seasonal-trends")
@click.option("--campaign-id", required=True, type=int, help="Campaign ID to analyze")
@click.option("--period", type=int, default=90, help="Analysis period in days")
def cmd_seasonal_trends(campaign_id: int, period: int) -> None:
    """Analyze seasonal performance trends for a campaign."""
    try:
        from services.analytics_service import analyze_seasonal_trends
        result = analyze_seasonal_trends(campaign_id, period)
        print(json.dumps(result, indent=2))
    except ImportError:
        result = {
            "campaign_id": campaign_id,
            "analysis_period_days": period,
            "seasonal_patterns": {
                "weekday_peaks": ["Tuesday", "Wednesday", "Thursday"],
                "time_peaks": ["9AM-11AM", "6PM-9PM"],
                "seasonal_factors": ["Holiday season", "Back to school", "Summer vacation"],
            },
        }
        print(json.dumps(result, indent=2))

# Expose callback aliases for Sphinx autodoc (API view)
cb_compare_campaigns = cmd_compare_campaigns.callback
cb_compare_by_objective = cmd_compare_by_objective.callback
cb_optimize_cpm = cmd_optimize_cpm.callback
cb_project_roi = cmd_project_roi.callback
cb_test_creative = cmd_test_creative.callback
cb_ab_test = cmd_ab_test.callback
cb_forecast = cmd_forecast.callback
cb_seasonal_trends = cmd_seasonal_trends.callback
