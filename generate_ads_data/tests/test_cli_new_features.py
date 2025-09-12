"""
Tests for new CLI features following TDD principles.

This module tests the new streamlined CLI commands including:
- list-campaigns
- export-campaign
- compare-campaigns
- compare-by-objective
- optimize-cpm
- project-roi
- test-creative
- ab-test
- forecast
- seasonal-trends
- status
"""

import json
import os
import sqlite3
import tempfile
from unittest.mock import Mock, patch, MagicMock
import pytest
from click.testing import CliRunner

# Import the CLI commands
from cli import cli


class TestListCampaigns:
    """Test the list-campaigns command."""

    def test_list_campaigns_table_format(self, runner, mock_db):
        """Test table format output for campaigns."""
        result = runner.invoke(cli, ["campaign", "list", "--format", "table"])
        assert result.exit_code == 0
        assert "📊 Campaign List" in result.output
        assert "ID" in result.output
        assert "Name" in result.output
        assert "Objective" in result.output

    def test_list_campaigns_json_format(self, runner, mock_db):
        """Test JSON format output for campaigns."""
        result = runner.invoke(cli, ["campaign", "list", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "name" in data[0]

    def test_list_campaigns_csv_format(self, runner, mock_db):
        """Test CSV format output for campaigns."""
        result = runner.invoke(cli, ["campaign", "list", "--format", "csv"])
        assert result.exit_code == 0
        assert "ID,Name,Objective,Status,Target CPM,DSP Partner" in result.output

    def test_list_campaigns_with_objective_filter(self, runner, mock_db):
        """Test filtering campaigns by objective."""
        result = runner.invoke(cli, ["campaign", "list", "--objective", "AWARENESS"])
        assert result.exit_code == 0
        # Should only show AWARENESS campaigns

    def test_list_campaigns_with_status_filter(self, runner, mock_db):
        """Test filtering campaigns by status."""
        result = runner.invoke(cli, ["campaign", "list", "--status", "ACTIVE"])
        assert result.exit_code == 0
        # Should only show ACTIVE campaigns

    def test_list_campaigns_no_database(self, runner):
        """Test behavior when database doesn't exist."""
        # Mock the campaign service to return empty list when database doesn't exist
        with patch('services.campaign_service.list_campaigns') as mock_list:
            mock_list.return_value = []

            result = runner.invoke(cli, ["campaign", "list"])
            assert result.exit_code == 0
            # When service returns empty list, CLI should show empty table
            assert "📊 Campaign List" in result.output


class TestExportCampaign:
    """Test the export-campaign command."""

    def test_export_campaign_json_format(self, runner, mock_db):
        """Test JSON export format."""
        result = runner.invoke(cli, ["campaign", "export", "--id", "1", "--format", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "campaign_id" in data
        assert "campaign_data" in data
        assert "line_items_count" in data

    def test_export_campaign_csv_format(self, runner, mock_db):
        """Test CSV export format."""
        result = runner.invoke(cli, ["campaign", "export", "--id", "1", "--format", "csv"])
        assert result.exit_code == 0
        assert "Field,Value" in result.output

    def test_export_campaign_with_performance(self, runner, mock_db):
        """Test export including performance data."""
        result = runner.invoke(cli, ["campaign", "export", "--id", "1", "--include-performance"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["performance_records"] > 0

    def test_export_campaign_without_performance(self, runner, mock_db):
        """Test export excluding performance data."""
        result = runner.invoke(cli, ["campaign", "export", "--id", "1", "--no-include-performance"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["performance_records"] == 0

    def test_export_campaign_not_found(self, runner):
        """Test export for non-existent campaign."""
        # Mock the export service to raise an error for campaign 999
        with patch('services.export_service.export_campaign') as mock_export:
            mock_export.side_effect = ValueError("Campaign 999 not found")

            result = runner.invoke(cli, ["campaign", "export", "--id", "999"])
            assert result.exit_code == 0
            assert "❌ Campaign 999 not found" in result.output


class TestCompareCampaigns:
    """Test the compare-campaigns command."""

    def test_compare_campaigns_basic(self, runner, mock_db):
        """Test basic campaign comparison."""
        result = runner.invoke(cli, ["compare-campaigns", "--campaign1", "1", "--campaign2", "2"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "campaign_1" in data
        assert "campaign_2" in data
        assert "comparison" in data

    def test_compare_campaigns_with_custom_metrics(self, runner, mock_db):
        """Test comparison with custom metrics."""
        result = runner.invoke(cli, ["compare-campaigns", "--campaign1", "1", "--campaign2", "2", "--metrics", "cpm,ctr"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "comparison" in data

    def test_compare_campaigns_one_not_found(self, runner):
        """Test comparison when one campaign doesn't exist."""
        # Mock the comparison service to raise an error when one campaign is not found
        with patch('services.comparison_service.compare_campaigns') as mock_compare:
            mock_compare.side_effect = ValueError("One or both campaigns not found. Found: 1")

            result = runner.invoke(cli, ["compare-campaigns", "--campaign1", "1", "--campaign2", "999"])
            assert result.exit_code == 0
            assert "❌ One or both campaigns not found" in result.output


class TestCompareByObjective:
    """Test the compare-by-objective command."""

    def test_compare_by_objective_basic(self, runner, mock_db):
        """Test basic objective-based comparison."""
        result = runner.invoke(cli, ["compare-by-objective", "--objective", "AWARENESS"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "objective" in data
        assert "total_campaigns" in data
        assert "campaigns" in data

    def test_compare_by_objective_with_top_n(self, runner, mock_db):
        """Test objective comparison with top N limit."""
        result = runner.invoke(cli, ["compare-by-objective", "--objective", "AWARENESS", "--top-n", "3"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["campaigns"]) <= 3

    def test_compare_by_objective_no_campaigns(self, runner):
        """Test objective comparison when no campaigns exist."""
        # Mock the database to return no campaigns for NONEXISTENT objective
        with patch('os.path.exists', return_value=True):
            with patch('sqlite3.connect') as mock_connect:
                mock_conn = Mock()
                mock_cursor = Mock()
                mock_connect.return_value = mock_conn
                mock_conn.cursor.return_value = mock_cursor

                # Mock no campaigns found for NONEXISTENT objective
                mock_cursor.fetchall.return_value = []

                result = runner.invoke(cli, ["compare-by-objective", "--objective", "NONEXISTENT"])
                assert result.exit_code == 0
                # The service returns a structured response with a message
                assert "No campaigns found with objective: NONEXISTENT" in result.output


class TestOptimizeCpm:
    """Test the optimize-cpm command."""

    def test_optimize_cpm_awareness(self, runner):
        """Test CPM optimization for AWARENESS objective."""
        result = runner.invoke(cli, ["optimize-cpm", "--budget", "10000", "--objective", "AWARENESS"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "suggested_cpm" in data
        assert "estimated_impressions" in data
        assert "budget_efficiency" in data

    def test_optimize_cpm_consideration(self, runner):
        """Test CPM optimization for CONSIDERATION objective."""
        result = runner.invoke(cli, ["optimize-cpm", "--budget", "15000", "--objective", "CONSIDERATION"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["suggested_cpm"] > 0

    def test_optimize_cpm_conversion(self, runner):
        """Test CPM optimization for CONVERSION objective."""
        result = runner.invoke(cli, ["optimize-cpm", "--budget", "20000", "--objective", "CONVERSION"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["suggested_cpm"] > 0

    def test_optimize_cpm_with_target_impressions(self, runner):
        """Test CPM optimization with target impressions."""
        result = runner.invoke(cli, ["optimize-cpm", "--budget", "10000", "--objective", "AWARENESS", "--target-impressions", "500000"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "suggested_cpm" in data


class TestProjectRoi:
    """Test the project-roi command."""

    def test_project_roi_basic(self, runner):
        """Test basic ROI projection."""
        result = runner.invoke(cli, ["project-roi", "--campaign-id", "1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "campaign_id" in data
        assert "scenarios" in data

    def test_project_roi_with_scenarios(self, runner):
        """Test ROI projection with custom scenario count."""
        result = runner.invoke(cli, ["project-roi", "--campaign-id", "1", "--scenarios", "5"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["scenarios"]) == 5

    def test_project_roi_with_optimistic(self, runner):
        """Test ROI projection including optimistic scenario."""
        result = runner.invoke(cli, ["project-roi", "--campaign-id", "1", "--optimistic"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        optimistic_scenarios = [s for s in data["scenarios"] if "Optimistic" in s["name"]]
        assert len(optimistic_scenarios) > 0


class TestTestCreative:
    """Test the test-creative command."""

    def test_test_creative_basic(self, runner):
        """Test basic creative testing."""
        result = runner.invoke(cli, ["test-creative", "--format", "video"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "format" in data
        assert "recommendations" in data

    def test_test_creative_with_duration(self, runner):
        """Test creative testing with duration."""
        result = runner.invoke(cli, ["test-creative", "--format", "video", "--duration", "30"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["duration"] == 30

    def test_test_creative_interactive(self, runner):
        """Test creative testing with interactive flag."""
        result = runner.invoke(cli, ["test-creative", "--format", "banner", "--interactive"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["interactive"] is True


class TestAbTest:
    """Test the ab-test command."""

    def test_ab_test_basic(self, runner):
        """Test basic A/B test setup."""
        result = runner.invoke(cli, ["ab-test", "--variant-a", "Control", "--variant-b", "Test"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "variant_a" in data
        assert "variant_b" in data
        assert "setup_instructions" in data

    def test_ab_test_with_duration(self, runner):
        """Test A/B test setup with custom duration."""
        result = runner.invoke(cli, ["ab-test", "--variant-a", "Control", "--variant-b", "Test", "--test-duration", "21"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["test_duration_days"] == 21


class TestForecast:
    """Test the forecast command."""

    def test_forecast_basic(self, runner):
        """Test basic performance forecasting."""
        result = runner.invoke(cli, ["forecast", "--campaign-id", "1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "campaign_id" in data
        assert "projected_metrics" in data

    def test_forecast_with_days(self, runner):
        """Test forecasting with custom period."""
        result = runner.invoke(cli, ["forecast", "--campaign-id", "1", "--days", "60"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["forecast_days"] == 60

    def test_forecast_without_seasonal(self, runner):
        """Test forecasting without seasonal adjustments."""
        result = runner.invoke(cli, ["forecast", "--campaign-id", "1", "--no-include-seasonal"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "projected_metrics" in data


class TestSeasonalTrends:
    """Test the seasonal-trends command."""

    def test_seasonal_trends_basic(self, runner):
        """Test basic seasonal trend analysis."""
        result = runner.invoke(cli, ["seasonal-trends", "--campaign-id", "1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "campaign_id" in data
        assert "seasonal_patterns" in data

    def test_seasonal_trends_with_period(self, runner):
        """Test seasonal analysis with custom period."""
        result = runner.invoke(cli, ["seasonal-trends", "--campaign-id", "1", "--period", "180"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["analysis_period_days"] == 180


class TestStatus:
    """Test the status command."""

    def test_status_basic(self, runner, mock_db):
        """Test basic status check."""
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "database" in data
        assert "system" in data
        assert "campaigns" in data

    def test_status_no_database(self, runner):
        """Test status when database doesn't exist."""
        with patch('os.path.exists', return_value=False):
            result = runner.invoke(cli, ["status"])
            assert result.exit_code == 0
            data = json.loads(result.output)
            assert data["database"]["status"] == "not_found"


# Fixtures
@pytest.fixture
def runner():
    """CLI runner fixture."""
    return CliRunner()

@pytest.fixture
def mock_db():
    """Mock database fixture with sample data."""
    # Patch the services directly to return mock data
    with patch('services.campaign_service.list_campaigns') as mock_list_campaigns:
        with patch('services.export_service.export_campaign') as mock_export_campaign:
            with patch('services.comparison_service.compare_campaigns') as mock_compare_campaigns:
                with patch('services.comparison_service.compare_by_objective') as mock_compare_by_objective:
                    # Set up mock service responses
                    mock_list_campaigns.return_value = [
                        {"id": 1, "name": "Test Campaign 1", "objective": "AWARENESS", "status": "ACTIVE", "target_cpm": 15.50, "dsp_partner": "Test DSP"},
                        {"id": 2, "name": "Test Campaign 2", "objective": "CONSIDERATION", "status": "ACTIVE", "target_cpm": 25.00, "dsp_partner": "Test DSP"}
                    ]

                    # Mock export service to handle different formats
                    def mock_export_campaign_side_effect(campaign_id, format, include_performance):
                        if format == "csv":
                            return {"csv_data": "Field,Value\ncampaign_id,1\ncampaign_data.name,Test Campaign 1", "format": "csv"}
                        else:
                            return {
                                "campaign_id": 1,
                                "campaign_data": {
                                    "name": "Test Campaign 1",
                                    "status": "ACTIVE",
                                    "created_at": "2024-01-01",
                                    "updated_at": "2024-01-01",
                                    "objective": "AWARENESS",
                                    "currency": "USD",
                                    "target_cpm": 15.50,
                                    "dsp_partner": "Test DSP",
                                    "advertiser": "Test Advertiser",
                                    "brand": "Test Brand"
                                },
                                "line_items_count": 1,
                                "creatives_count": 1,
                                "performance_records": 1 if include_performance else 0
                            }

                    mock_export_campaign.side_effect = mock_export_campaign_side_effect

                    mock_compare_campaigns.return_value = {
                        "campaign_1": {
                            "id": 1,
                            "name": "Test Campaign 1",
                            "objective": "AWARENESS",
                            "target_cpm": 15.50,
                            "dsp_partner": "Test DSP"
                        },
                        "campaign_2": {
                            "id": 2,
                            "name": "Test Campaign 2",
                            "objective": "CONSIDERATION",
                            "target_cpm": 25.00,
                            "dsp_partner": "Test DSP"
                        },
                        "comparison": {
                            "cpm_difference": 9.50,
                            "same_objective": False,
                            "same_dsp": True
                        }
                    }

                    mock_compare_by_objective.return_value = {
                        "objective": "AWARENESS",
                        "total_campaigns": 1,
                        "campaigns": [
                            {
                                "id": 1,
                                "name": "Test Campaign 1",
                                "target_cpm": 15.50,
                                "status": "ACTIVE",
                                "dsp_partner": "Test DSP"
                            }
                        ]
                    }

                    yield mock_db


@pytest.fixture
def mock_db_fallback():
    """Mock database fixture for fallback scenarios."""
    # Patch the database path to not exist
    with patch('os.path.exists', return_value=False):
        yield None


@pytest.fixture
def mock_db_campaign_not_found():
    """Mock database fixture for campaign not found scenarios."""
    with patch('os.path.exists', return_value=True):
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_connect.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Mock campaign not found
            mock_cursor.fetchone.return_value = None
            mock_cursor.fetchall.return_value = []

            yield mock_db_campaign_not_found
