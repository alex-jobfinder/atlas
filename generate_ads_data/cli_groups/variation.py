from __future__ import annotations

import json
from typing import Optional

import click


@click.group(help="Variations and templates: create and list.")
def variation() -> None:
    """Variation subcommands group."""
    pass


@variation.command("create")
@click.option("--template", required=True, type=str, help="Template name to use")
@click.option("--custom-rules", type=str, help="JSON string of custom variation rules")
@click.option("--seed", type=int, help="Random seed for reproducible variations")
@click.option("--output-format", type=click.Choice(["json", "csv"]), default="json", help="Output format")
def cmd_create_variations(template: str, custom_rules: Optional[str], seed: Optional[int], output_format: str) -> None:
    """Create automated campaign variations from a template.

    Args:
        template (str): Template name to use.
        custom_rules (str, optional): JSON string of custom variation rules.
        seed (int, optional): Random seed for reproducible variation generation.
        output_format (str): Output format: "json" or "csv".

    Returns:
        None. Prints the generated variations in the requested format.

    Examples:
        CLI:
            $ python cli.py create-variations --template baseline --output-format csv
    """
    try:
        from services.campaign_variation_service import EnhancedCampaignVariationService

        service = EnhancedCampaignVariationService()

        parsed_rules = None
        if custom_rules:
            parsed_rules = json.loads(custom_rules)

        variations = service.create_variations_from_template(template, parsed_rules, seed)

        if output_format == "json":
            print(json.dumps({
                "template": template,
                "variations_count": len(variations),
                "variations": variations
            }, indent=2))
        elif output_format == "csv":
            import csv
            import sys
            writer = csv.writer(sys.stdout)
            writer.writerow(["Variation", "Name", "Objective", "Target CPM", "Devices", "Formats"])
            for i, var in enumerate(variations):
                writer.writerow([
                    i + 1,
                    var.get("name", ""),
                    var.get("objective", ""),
                    var.get("line_items", [{}])[0].get("bid_cpm", ""),
                    str(var.get("targeting", {}).get("device", [])),
                    var.get("line_items", [{}])[0].get("ad_format", "")
                ])
    except ImportError:
        print("❌ Campaign variation service not available")
        print("💡 This feature requires additional dependencies")
    except Exception as e:
        print(f"❌ Failed to create variations: {e}")


@variation.command("list")
@click.option("--output-format", type=click.Choice(["json", "table"]), default="table", help="Output format")
def cmd_list_templates(output_format: str) -> None:
    """List available campaign variation templates.

    Args:
        output_format (str): Output format: "json" or "table".

    Returns:
        None. Prints available templates in the requested format.

    Examples:
        CLI:
            $ python cli.py list-templates --output-format json
    """
    try:
        from services.campaign_variation_service import EnhancedCampaignVariationService

        service = EnhancedCampaignVariationService()
        templates = service.get_template_metadata()

        if output_format == "json":
            print(json.dumps(templates, indent=2))
        else:
            from rich.console import Console
            from rich.table import Table

            console = Console()
            table = Table(title="🎯 Available Campaign Templates")
            table.add_column("Name", style="cyan")
            table.add_column("Profile", style="green")
            table.add_column("Variations", style="yellow")
            table.add_column("Budget Range", style="magenta")
            table.add_column("Description", style="white")

            for template in templates:
                budget_range = template.get("estimated_budget_range", {})
                budget_str = f"${budget_range.get('min', 0):,.0f} - ${budget_range.get('max', 0):,.0f}"
                table.add_row(
                    template["name"],
                    template["profile"],
                    str(template["variations_count"]),
                    budget_str,
                    template["description"]
                )

            console.print(table)
    except ImportError:
        print("❌ Campaign variation service not available")
    except Exception as e:
        print(f"❌ Failed to list templates: {e}")


# Expose callback aliases for Sphinx autodoc (API view)
cb_create_variations = cmd_create_variations.callback
cb_list_templates = cmd_list_templates.callback
