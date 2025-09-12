"""
CLI entrypoints for DB initialization and demo data creation.

The CLI is composed from modular subcommand groups in `cli_groups/`.
Root-level command names are preserved via aliases for backward
compatibility, while grouped commands enable a cleaner structure.
"""
from __future__ import annotations

import click

# Domain groups (Click Group objects)
from cli_groups import db as db_group
from cli_groups import campaign as campaign_group
from cli_groups import analysis as analysis_group
from cli_groups import variation as variation_group
from cli_groups import system as system_group

# Import command objects from groups to expose root-level aliases and keep
# Sphinx autodoc references (e.g., cli.cmd_init_db) intact.
from cli_groups.db import cmd_init_db, cmd_migrate_db
from cli_groups.campaign import (
    cmd_create_advertiser,
    cmd_create_campaign,
    cmd_generate_performance,
    cmd_generate_performance_ext,
    cmd_create_example,
    cmd_test_fields,
    cmd_create_profile,
    cmd_test_scenario,
    cmd_list_campaigns,
    cmd_export_campaign,
)
from cli_groups.analysis import (
    cmd_compare_campaigns,
    cmd_compare_by_objective,
    cmd_optimize_cpm,
    cmd_project_roi,
    cmd_test_creative,
    cmd_ab_test,
    cmd_forecast,
    cmd_seasonal_trends,
)
from cli_groups.variation import cmd_create_variations, cmd_list_templates
from cli_groups.system import cmd_show_schemas, cmd_status


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(package_name="generate-ads-data", prog_name="generate-ads-data")
def cli() -> None:
    """Root command group for ads demo utilities.

    Use ``-h/--help`` on any command to see options and defaults.
    """
    pass


# Register groups on the root
cli.add_command(db_group, name="db")
cli.add_command(campaign_group, name="campaign")
cli.add_command(analysis_group, name="analysis")
cli.add_command(variation_group, name="variation")
cli.add_command(system_group, name="system")


# Root-level aliases for streamlined UX expected by tests/docs
# Analysis/insights commands
cli.add_command(cmd_compare_campaigns, name="compare-campaigns")
cli.add_command(cmd_compare_by_objective, name="compare-by-objective")
cli.add_command(cmd_optimize_cpm, name="optimize-cpm")
cli.add_command(cmd_project_roi, name="project-roi")
cli.add_command(cmd_test_creative, name="test-creative")
cli.add_command(cmd_ab_test, name="ab-test")
cli.add_command(cmd_forecast, name="forecast")
cli.add_command(cmd_seasonal_trends, name="seasonal-trends")

# System status shortcut
cli.add_command(cmd_status, name="status")

# Back-compat root aliases for DB and campaign builders
cli.add_command(cmd_init_db, name="init-db")
cli.add_command(cmd_migrate_db, name="migrate-db")
cli.add_command(cmd_create_advertiser, name="create-advertiser")
cli.add_command(cmd_create_campaign, name="create-campaign")

# Campaign management commands
cli.add_command(cmd_generate_performance, name="generate-performance")
cli.add_command(cmd_generate_performance_ext, name="generate-performance-ext")
cli.add_command(cmd_create_example, name="create-example")
cli.add_command(cmd_test_fields, name="test-fields")
cli.add_command(cmd_create_profile, name="create-profile")
cli.add_command(cmd_test_scenario, name="test-scenario")
cli.add_command(cmd_list_campaigns, name="list-campaigns")
cli.add_command(cmd_export_campaign, name="export-campaign")

# Variation and template commands
cli.add_command(cmd_create_variations, name="create-variations")
cli.add_command(cmd_list_templates, name="list-templates")

# System and schema commands
cli.add_command(cmd_show_schemas, name="show-schemas")


if __name__ == "__main__":
    cli()
