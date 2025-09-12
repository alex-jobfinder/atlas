# from __future__ import annotations

# from typing import Optional

# import click
# from rich.console import Console
# from rich.panel import Panel
# from rich.progress import Progress, SpinnerColumn, TextColumn
# from rich.table import Table


# @click.group(help="Database operations: init and migrate.")
# def db() -> None:
#     """Root DB command group."""
#     pass

# # Initialize Rich console
# console = Console()


# @db.command("init")
# @click.option("--log-level", type=str, required=False, help="Log verbosity (e.g., INFO, DEBUG).")
# @click.option("--db-url", type=str, required=False, help="Database URL (e.g., sqlite:///ads.db).")
# @click.option("--seed", type=int, required=False, help="Random seed for reproducible generation.")
# def cmd_init_db(log_level: Optional[str] = None, db_url: Optional[str] = None, seed: Optional[int] = None) -> None:
#     """Initialize a fresh database using the configured URL.

#     Args:
#         log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
#         db_url (str, optional): Database URL such as "sqlite:///ads.db".
#         seed (int, optional): Random seed for reproducibility when generating data.

#     Returns:
#         None

#     Examples:
#         CLI:
#             $ python cli.py db init --db-url sqlite:///ads.db --log-level INFO --seed 42
#     """
#     # Show configuration table
#     table = Table(title="🗄️ Database Initialization")
#     table.add_column("Setting", style="cyan")
#     table.add_column("Value", style="green")
#     table.add_row("Database URL", db_url or "sqlite:///ads.db")
#     table.add_row("Log Level", log_level or "INFO")
#     table.add_row("Seed", str(seed or 42))

#     console.print(table)
#     console.print()

#     # Local imports to avoid side-effects during docs build
#     from db_utils import setup_env, init_db, get_logger

#     with Progress(
#         SpinnerColumn(),
#         TextColumn("[progress.description]{task.description}"),
#         console=console,
#     ) as progress:
#         task = progress.add_task("Initializing database...", total=None)

#         setup_env(log_level, db_url, seed)
#         init_db()
#         get_logger(__name__).info("Initialized SQLite database")

#         progress.update(task, description="✅ Database initialized successfully!")

#     console.print(Panel("🎉 Database initialization completed!", style="green"))


# @db.command("migrate")
# @click.option("--log-level", type=str, required=False, help="Log verbosity (e.g., INFO, DEBUG).")
# @click.option("--db-url", type=str, required=False, help="Database URL (e.g., sqlite:///ads.db).")
# def cmd_migrate_db(log_level: Optional[str] = None, db_url: Optional[str] = None) -> None:
#     """Apply database migrations for the current schema version.

#     Args:
#         log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
#         db_url (str, optional): Database URL such as "sqlite:///ads.db".

#     Returns:
#         None

#     Examples:
#         CLI:
#             $ python cli.py db migrate --db-url sqlite:///ads.db --log-level INFO
#     """
#     # Show configuration table
#     table = Table(title="🔄 Database Migration")
#     table.add_column("Setting", style="cyan")
#     table.add_column("Value", style="green")
#     table.add_row("Database URL", db_url or "sqlite:///ads.db")
#     table.add_row("Log Level", log_level or "INFO")

#     console.print(table)
#     console.print()

#     from db_utils import setup_env, migrate_db, get_logger

#     with Progress(
#         SpinnerColumn(),
#         TextColumn("[progress.description]{task.description}"),
#         console=console,
#     ) as progress:
#         task = progress.add_task("Applying database migrations...", total=None)

#         setup_env(log_level, db_url)
#         get_logger(__name__).info("Applying DB migrations")
#         migrate_db()
#         get_logger(__name__).info("Applied migrations")

#         progress.update(task, description="✅ Database migrations completed!")

#     console.print(Panel("🎉 Database migration completed!", style="green"))

# # Expose callback aliases for Sphinx autodoc (API view)
# cb_init_db = cmd_init_db.callback
# cb_migrate_db = cmd_migrate_db.callback
