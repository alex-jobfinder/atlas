from __future__ import annotations

import json
from typing import Optional

import click


@click.group(help="Campaign operations: create, list, export, and performance.")
def campaign() -> None:
    """Campaign subcommands group."""
    pass


@campaign.command("create-advertiser")
@click.option("--name", required=False, type=str, help="Advertiser name (omit with --auto).")
@click.option("--email", required=False, type=str, help="Contact email (omit with --auto).")
@click.option("--brand", required=False, type=str, help="Brand name, if applicable.")
@click.option("--agency", required=False, type=str, help="Agency name, if applicable.")
@click.option("--auto", is_flag=True, default=False, help="Generate advertiser fields automatically.")
@click.option("--log-level", type=str, required=False, help="Log verbosity (e.g., INFO, DEBUG).")
@click.option("--db-url", type=str, required=False, help="Database URL (e.g., sqlite:///ads.db).")
@click.option("--seed", type=int, required=False, help="Random seed for reproducible generation.")
def cmd_create_advertiser(
    name: Optional[str],
    email: Optional[str],
    brand: Optional[str],
    agency: Optional[str],
    auto: bool,
    log_level: Optional[str] = None,
    db_url: Optional[str] = None,
    seed: Optional[int] = None,
) -> None:
    """Create an advertiser; use --auto or provide name and email.

    If ``--auto`` is set or required fields are missing, a realistic
    advertiser is generated using faker providers.

    Args:
        name (str, optional): Advertiser name when not using ``--auto``.
        email (str, optional): Contact email when not using ``--auto``.
        brand (str, optional): Brand name, if applicable.
        agency (str, optional): Agency name, if applicable.
        auto (bool): Generate an advertiser automatically if true.
        log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
        db_url (str, optional): Database URL such as "sqlite:///ads.db".
        seed (int, optional): Random seed for reproducibility.

    Returns:
        None. Prints a JSON object with the created ``advertiser_id`` to stdout.

    Examples:
        Auto-generated advertiser:
            $ python cli.py campaign create-advertiser --auto

        Specify fields manually:
            $ python cli.py campaign create-advertiser --name "Acme" --email acct@acme.com
    """
    from db_utils import setup_env
    from factories.faker_providers import fake_advertiser
    from models.registry import registry
    from services.generator import create_advertiser_payload
    from db_utils import session_scope

    setup_env(log_level, db_url, seed)
    if auto or not (name and email):
        n, e, b, a = fake_advertiser()
        name = name or n
        email = email or e
        brand = brand or b
        agency = agency or a
    payload = registry.AdvertiserCreate(name=name or "", contact_email=email or "", brand=brand, agency_name=agency)
    adv = create_advertiser_payload(payload)
    with session_scope() as s:
        s.add(adv)
        s.flush()
        print(json.dumps({"advertiser_id": adv.id}))


@campaign.command("create")
@click.option("--advertiser-id", required=True, type=int, help="ID of the advertiser that owns the campaign.")
@click.option("--auto", is_flag=True, default=False, help="Generate a demo campaign automatically (required in v1).")
@click.option(
    "--profile",
    type=click.Choice(["AWARENESS", "CONSIDERATION", "CONVERSION"]),
    help="Optional campaign profile to guide generation.",
)
@click.option("--log-level", type=str, required=False, help="Log verbosity (e.g., INFO, DEBUG).")
@click.option("--db-url", type=str, required=False, help="Database URL (e.g., sqlite:///ads.db).")
@click.option("--seed", type=int, required=False, help="Random seed for reproducible generation.")
@click.option(
    "--generate-performance/--no-generate-performance",
    default=False,
    show_default=True,
    help="Generate synthetic performance rows for the new campaign.",
)
def cmd_create_campaign(
    advertiser_id: Optional[int],
    auto: bool,
    profile: Optional[str] = None,
    log_level: Optional[str] = None,
    db_url: Optional[str] = None,
    seed: Optional[int] = None,
    generate_performance: bool = False,
) -> None:
    """Create a demo campaign for an advertiser; requires ``--auto`` for v1.

    Persists a demo campaign for the given advertiser. When
    ``--generate-performance`` is provided, synthetic hourly performance is
    generated for the new campaign.

    Args:
        advertiser_id (int): The advertiser ID to attach the campaign to.
        auto (bool): Must be true for v1; generates a demo campaign.
        profile (str, optional): Campaign profile (AWARENESS, CONSIDERATION, CONVERSION).
        log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
        db_url (str, optional): Database URL such as "sqlite:///ads.db".
        seed (int, optional): Random seed for reproducibility.
        generate_performance (bool): Generate performance rows for the new campaign.

    Returns:
        None

    Raises:
        click.UsageError: If ``--auto`` is not provided.

    Examples:
        Create campaign and performance:
            $ python cli.py campaign create --advertiser-id 1 --auto \
                --profile AWARENESS --generate-performance
    """
    from db_utils import setup_env, persist_campaign, generate_hourly_performance
    from db_utils import build_auto_campaign

    setup_env(log_level, db_url, seed)
    if not auto:
        raise click.UsageError("For v1, use --auto to generate a demo campaign")
    campaign_obj = build_auto_campaign(advertiser_id, profile)  # type: ignore[arg-type]
    result = persist_campaign(advertiser_id, campaign_obj, return_ids=True)
    if generate_performance and isinstance(result, dict):
        cid = result.get("campaign_id")
        if cid is not None:
            _ = generate_hourly_performance(int(cid), seed=seed, replace=True)


@campaign.command("generate-performance")
@click.option("--campaign-id", required=True, type=int, help="Campaign ID to generate performance for.")
@click.option("--seed", required=False, type=int, help="Random seed for reproducibility.")
@click.option("--replace/--no-replace", default=True, show_default=True, help="Replace existing rows if present.")
def cmd_generate_performance(campaign_id: int, seed: Optional[int] = None, replace: bool = True) -> None:
    """Generate synthetic hourly performance rows for a campaign.

    Args:
        campaign_id (int): Campaign identifier.
        seed (int, optional): Random seed for reproducibility.
        replace (bool): If true, existing rows are replaced.

    Returns:
        None. Prints a JSON summary of generated performance rows.

    Examples:
        CLI:
            $ python cli.py campaign generate-performance --campaign-id 42 --seed 123 --no-replace
    """
    from db_utils import generate_performance

    result = generate_performance(campaign_id, seed=seed, replace=replace)
    print(json.dumps(result))


@campaign.command("generate-performance-ext")
@click.option("--campaign-id", required=True, type=int, help="Campaign ID to generate extended performance for.")
@click.option("--seed", required=False, type=int, help="Random seed for reproducibility.")
@click.option("--replace/--no-replace", default=True, show_default=True, help="Replace existing rows if present.")
def cmd_generate_performance_ext(campaign_id: int, seed: Optional[int] = None, replace: bool = True) -> None:
    """Generate synthetic hourly extended performance rows for a campaign.

    Args:
        campaign_id (int): Campaign identifier.
        seed (int, optional): Random seed for reproducibility.
        replace (bool): If true, existing rows are replaced.

    Returns:
        None. Prints a JSON object describing the result to stdout.

    Examples:
        CLI:
            $ python cli.py campaign generate-performance-ext --campaign-id 42 --seed 7
    """
    from services.performance_ext import generate_hourly_performance_ext

    rows = generate_hourly_performance_ext(campaign_id, seed=seed, replace=True)
    print(json.dumps({"campaign_id": campaign_id, "rows": rows, "type": "extended"}))


@campaign.command("create-example")
@click.option("--template", required=True, type=str, help="Path to template file")
@click.option("--example", required=True, type=str, help="Name of example to generate")
@click.option("--seed", type=int, help="Seed for reproducible generation")
@click.option("--performance-only", is_flag=True, help="Generate only performance data for existing entities")
@click.option("--log-level", type=str, required=False)
@click.option("--db-url", type=str, required=False)
def cmd_create_example(
    template: str,
    example: str,
    seed: Optional[int] = None,
    performance_only: bool = False,
    log_level: Optional[str] = None,
    db_url: Optional[str] = None,
) -> None:
    """Create a complete example from a template, optionally generating performance.

    Args:
        template (str): Path to the template file to use.
        example (str): Name for the example to generate.
        seed (int, optional): Random seed for reproducibility.
        performance_only (bool): Only generate performance for existing entities.
        log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
        db_url (str, optional): Database URL such as "sqlite:///ads.db".

    Returns:
        None. Prints a JSON summary of created entities.

    Raises:
        click.UsageError: If the example processor is not available.

    Examples:
        CLI:
            $ python cli.py campaign create-example --template examples/netflix.yml \
                --example my-demo --seed 123
    """
    from db_utils import setup_env

    setup_env(log_level, db_url, seed)
    try:
        from services.processor import create_example_from_template

        result = create_example_from_template(template, example, performance_only=performance_only)
        print(json.dumps(result, indent=2))
    except ImportError:
        print("Streamlined processor not implemented yet. Use create-from-config instead.")
        print("Example: python cli.py create-from-config --path config.yml --generate-performance")
        raise click.UsageError("Streamlined processor not available")


@campaign.command("test-fields")
@click.option("--template", required=True, type=str, help="Path to field testing template")
@click.option("--focus", required=True, type=str, help="Comma-separated list of fields to test")
@click.option("--seed", type=int, help="Seed for reproducible generation")
@click.option("--auto-performance/--no-auto-performance", default=True, help="Auto-generate performance data")
@click.option("--log-level", type=str, required=False)
@click.option("--db-url", type=str, required=False)
def cmd_test_fields(
    template: str,
    focus: str,
    seed: Optional[int] = None,
    auto_performance: bool = True,
    log_level: Optional[str] = None,
    db_url: Optional[str] = None,
) -> None:
    """Test specific fields while auto-generating realistic context.

    Args:
        template (str): Path to the field-testing template file.
        focus (str): Comma-separated list of fields to test (e.g., "name,budget").
        seed (int, optional): Random seed for reproducibility.
        auto_performance (bool): Auto-generate performance data in the scenario.
        log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
        db_url (str, optional): Database URL such as "sqlite:///ads.db".

    Returns:
        None. Prints a JSON result of the field tests.

    Raises:
        click.UsageError: If the test processor is not available.

    Examples:
        CLI:
            $ python cli.py campaign test-fields --template tests/fields.yml \
                --focus name,budget --no-auto-performance
    """
    from db_utils import setup_env

    setup_env(log_level, db_url, seed)
    try:
        from services.processor import test_specific_fields

        focus_fields = [f.strip() for f in focus.split(",")]
        result = test_specific_fields(template, focus_fields, auto_performance=auto_performance)
        print(json.dumps(result, indent=2))
    except ImportError:
        print("Streamlined processor not implemented yet. Use create-from-config instead.")
        print("Example: python cli.py create-from-config --path config.yml --generate-performance")
        raise click.UsageError("Streamlined processor not available")


@campaign.command("create-profile")
@click.option("--name", required=True, type=str, help="Profile name from campaign-profiles.yml")
@click.option("--test-fields", type=str, help="Comma-separated list of fields to override")
@click.option("--seed", type=int, help="Seed for reproducible generation")
@click.option("--performance-only", is_flag=True, help="Generate only performance data for existing entities")
@click.option("--log-level", type=str, required=False)
@click.option("--db-url", type=str, required=False)
def cmd_create_profile(
    name: str,
    test_fields: Optional[str] = None,
    seed: Optional[int] = None,
    performance_only: bool = False,
    log_level: Optional[str] = None,
    db_url: Optional[str] = None,
) -> None:
    """Create a campaign from a pre-built profile with smart defaults.

    Args:
        name (str): Profile name from ``campaign-profiles.yml``.
        test_fields (str, optional): Comma-separated key=value overrides.
        seed (int, optional): Random seed for reproducibility.
        performance_only (bool): Only create performance data for existing entities.
        log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
        db_url (str, optional): Database URL such as "sqlite:///ads.db".

    Returns:
        None. Prints a JSON summary of the created campaign.

    Raises:
        click.UsageError: If the profile processor is not available.

    Examples:
        CLI with overrides:
            $ python cli.py campaign create-profile --name AWARENESS_MINI \
                --test-fields "budget=5000,status=PAUSED"
    """
    from db_utils import setup_env

    setup_env(log_level, db_url, seed)
    try:
        from services.processor import create_campaign_from_profile

        override_fields = {}
        if test_fields:
            for field in test_fields.split(","):
                field = field.strip()
                if "=" in field:
                    key, value = field.split("=", 1)
                    override_fields[key.strip()] = value.strip()

        result = create_campaign_from_profile(name, override_fields, performance_only=performance_only)
        print(json.dumps(result, indent=2))
    except ImportError:
        print("Streamlined processor not implemented yet. Use create-from-config instead.")
        print("Example: python cli.py create-from-config --path config.yml --generate-performance")
        raise click.UsageError("Streamlined processor not available")


@campaign.command("test-scenario")
@click.option("--name", required=True, type=str, help="Scenario name from testing-scenarios.yml")
@click.option("--seed", type=int, help="Seed for reproducible generation")
@click.option("--log-level", type=str, required=False)
@click.option("--db-url", type=str, required=False)
def cmd_test_scenario(
    name: str, seed: Optional[int] = None, log_level: Optional[str] = None, db_url: Optional[str] = None
) -> None:
    """Test common scenarios with one command.

    Args:
        name (str): Scenario name from ``testing-scenarios.yml``.
        seed (int, optional): Random seed for reproducibility.
        log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
        db_url (str, optional): Database URL such as "sqlite:///ads.db".

    Returns:
        None. Prints a JSON result for the scenario.

    Raises:
        click.UsageError: If the scenario processor is not available.

    Examples:
        CLI:
            $ python cli.py campaign test-scenario --name invalid-targeting --seed 99
    """
    from db_utils import setup_env

    setup_env(log_level, db_url, seed)
    try:
        from services.processor import test_prebuilt_scenario

        result = test_prebuilt_scenario(name)
        print(json.dumps(result, indent=2))
    except ImportError:
        print("Streamlined processor not implemented yet. Use create-from-config instead.")
        print("Example: python cli.py create-from-config --path config.yml --generate-performance")
        raise click.UsageError("Streamlined processor not available")


@campaign.command("list")
@click.option("--format", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")
@click.option("--objective", type=str, help="Filter by campaign objective")
@click.option("--status", type=str, help="Filter by campaign status")
def cmd_list_campaigns(format: str, objective: Optional[str] = None, status: Optional[str] = None) -> None:
    """List all campaigns with optional filtering.

    Args:
        format (str): Output format: "table" (default), "json", or "csv".
        objective (str, optional): Filter by objective (e.g., AWARENESS).
        status (str, optional): Filter by status (e.g., ACTIVE, PAUSED).

    Returns:
        None. Prints the campaign list in the requested format.

    Examples:
        Table output:
            $ python cli.py campaign list

        JSON output with filters:
            $ python cli.py campaign list --format json --objective AWARENESS --status ACTIVE
    """
    try:
        from services.campaign_service import list_campaigns

        campaigns = list_campaigns(objective=objective, status=status)
        if format == "json":
            print(json.dumps(campaigns, indent=2))
        elif format == "csv":
            import csv
            import sys

            writer = csv.writer(sys.stdout)
            writer.writerow(["ID", "Name", "Objective", "Status", "Target CPM", "DSP Partner"])
            for campaign in campaigns:
                writer.writerow(
                    [
                        campaign.get("id"),
                        campaign.get("name"),
                        campaign.get("objective"),
                        campaign.get("status"),
                        campaign.get("target_cpm"),
                        campaign.get("dsp_partner"),
                    ]
                )
        else:
            print("📊 Campaign List")
            print("=" * 80)
            print(f"{'ID':<4} {'Name':<25} {'Objective':<15} {'Status':<10} {'CPM':<8} {'DSP':<12}")
            print("-" * 80)
            for campaign in campaigns:
                print(
                    f"{campaign.get('id', ''):<4} {campaign.get('name', '')[:24]:<25} "
                    f"{campaign.get('objective', '')[:14]:<15} {campaign.get('status', '')[:9]:<10} "
                    f"${campaign.get('target_cpm', 0):<7,.0f} {campaign.get('dsp_partner', '')[:11]:<12}"
                )
    except ImportError:
        try:
            import sqlite3
            import os
            if not os.path.exists("ads.db"):
                print("❌ Database not found. Please run './run_all.sh' first to create sample data.")
                return
            conn = sqlite3.connect("ads.db")
            cursor = conn.cursor()

            query = "SELECT id, name, objective, status, target_cpm, dsp_partner FROM campaigns"
            params: list[str] = []
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
            rows = cursor.fetchall()
            if format == "json":
                result = [
                    {
                        "id": row[0],
                        "name": row[1],
                        "objective": row[2],
                        "status": row[3],
                        "target_cpm": row[4],
                        "dsp_partner": row[5],
                    }
                    for row in rows
                ]
                print(json.dumps(result, indent=2))
            elif format == "csv":
                import csv
                import sys

                writer = csv.writer(sys.stdout)
                writer.writerow(["ID", "Name", "Objective", "Status", "Target CPM", "DSP Partner"])
                for row in rows:
                    writer.writerow(row)
            else:
                print("📊 Campaign List (Direct DB Query)")
                print("=" * 80)
                print(f"{'ID':<4} {'Name':<25} {'Objective':<15} {'Status':<10} {'CPM':<8} {'DSP':<12}")
                print("-" * 80)
                for row in rows:
                    name = row[1][:24] if row[1] else ""
                    objective = row[2][:14] if row[2] else ""
                    status = row[3][:9] if row[3] else ""
                    cpm = row[4] if row[4] else 0
                    dsp = row[5][:11] if row[5] else ""
                    print(f"{row[0]:<4} {name:<25} {objective:<15} {status:<10} ${cpm:<7,.0f} {dsp:<12}")
            conn.close()
        except Exception as e:
            print(f"❌ Database query failed: {e}")


@campaign.command("export")
@click.option("--id", required=True, type=int, help="Campaign ID to export")
@click.option("--format", type=click.Choice(["json", "csv", "excel"]), default="json", help="Export format")
@click.option(
    "--include-performance/--no-include-performance",
    default=True,
    show_default=True,
    help="Include performance data",
)
def cmd_export_campaign(id: int, format: str, include_performance: bool) -> None:
    """Export campaign data in various formats.

    Args:
        id (int): Campaign ID to export.
        format (str): Export format: "json", "csv", or "excel" (service-only).
        include_performance (bool): Include performance rows when true.

    Returns:
        None. Prints the exported representation to stdout.

    Examples:
        JSON export including performance:
            $ python cli.py campaign export --id 12 --format json --include-performance
    """
    try:
        from services.export_service import export_campaign

        try:
            result = export_campaign(id, format, include_performance)
            # If service returns a CSV-like payload, print in a consistent JSON envelope
            if isinstance(result, dict) and result.get("format") == "csv" and "csv_data" in result:
                print(json.dumps(result, indent=2))
            else:
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
                SELECT c.*, a.name as advertiser_name, a.brand
                FROM campaigns c
                JOIN advertisers a ON c.advertiser_id = a.id
                WHERE c.id = ?
                """,
                (id,),
            )
            campaign = cursor.fetchone()
            if not campaign:
                print(f"❌ Campaign {id} not found.")
                return

            cursor.execute("SELECT * FROM line_items WHERE campaign_id = ?", (id,))
            line_items = cursor.fetchall()

            if line_items:
                line_item_ids = [str(item[0]) for item in line_items]
                placeholders = ",".join(["?" for _ in line_item_ids])
                cursor.execute(f"SELECT * FROM creatives WHERE line_item_id IN ({placeholders})", line_item_ids)
                creatives = cursor.fetchall()
            else:
                creatives = []

            performance = []
            if include_performance:
                cursor.execute("SELECT * FROM campaign_performance WHERE campaign_id = ? LIMIT 100", (id,))
                performance = cursor.fetchall()

            conn.close()
            result = {
                "campaign_id": id,
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
                    "brand": campaign[-1],
                },
                "line_items_count": len(line_items),
                "creatives_count": len(creatives),
                "performance_records": len(performance) if include_performance else 0,
            }
            if format == "json":
                print(json.dumps(result, indent=2))
            elif format == "csv":
                import csv
                import sys
                writer = csv.writer(sys.stdout)
                writer.writerow(["Field", "Value"])
                for key, value in result.items():
                    if isinstance(value, dict):
                        for k, v in value.items():
                            writer.writerow([f"{key}.{k}", v])
                    else:
                        writer.writerow([key, value])
            else:
                print("Excel export not available in fallback mode. Use JSON or CSV.")
                print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"❌ Export failed: {e}")

cb_create_advertiser = cmd_create_advertiser.callback
cb_create_campaign = cmd_create_campaign.callback
cb_generate_performance = cmd_generate_performance.callback
cb_generate_performance_ext = cmd_generate_performance_ext.callback
cb_create_example = cmd_create_example.callback
cb_test_fields = cmd_test_fields.callback
cb_create_profile = cmd_create_profile.callback
cb_test_scenario = cmd_test_scenario.callback
cb_list_campaigns = cmd_list_campaigns.callback
cb_export_campaign = cmd_export_campaign.callback
