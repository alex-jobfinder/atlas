from __future__ import annotations

import json
import click


@click.group(help="System and metadata: schemas and status.")
def system() -> None:
    """System subcommands group."""
    pass


@system.command("schemas")
def cmd_show_schemas() -> None:
    """Show all database schemas and table structures.

    Returns:
        None. Prints schema information to stdout.

    Examples:
        CLI:
            $ python cli.py show-schemas
    """
    try:
        from services.erd_service import print_all_schemas
        print_all_schemas()
    except ImportError:
        print("❌ ERD service not available")
    except Exception as e:
        print(f"❌ Failed to show schemas: {e}")


@system.command("status")
def cmd_status() -> None:
    """Check system status and database health.

    Returns:
        None. Prints a JSON object summarizing database and system status.

    Examples:
        CLI:
            $ python cli.py status
    """
    import os
    import sqlite3

    status = {
        "database": {},
        "system": {},
        "campaigns": {},
    }

    if os.path.exists("ads.db"):
        try:
            conn = sqlite3.connect("ads.db")
            cursor = conn.cursor()

            tables = ["advertisers", "campaigns", "line_items", "creatives", "performance"]
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    status["campaigns"][table] = count
                except Exception:
                    status["campaigns"][table] = 0

            conn.close()
            status["database"]["status"] = "healthy"
            status["database"]["size_mb"] = round(os.path.getsize("ads.db") / (1024 * 1024), 2)
        except Exception as e:
            status["database"]["status"] = f"error: {str(e)}"
    else:
        status["database"]["status"] = "not_found"

    status["system"]["python_version"] = (
        f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
    )
    status["system"]["working_directory"] = os.getcwd()

    print(json.dumps(status, indent=2))


# Expose callback aliases for Sphinx autodoc (API view)
cb_show_schemas = cmd_show_schemas.callback
cb_status = cmd_status.callback
