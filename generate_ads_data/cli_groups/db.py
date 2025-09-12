from __future__ import annotations

from typing import Optional

import click


@click.group(help="Database operations: init and migrate.")
def db() -> None:
    """Root DB command group."""
    pass


@db.command("init")
@click.option("--log-level", type=str, required=False, help="Log verbosity (e.g., INFO, DEBUG).")
@click.option("--db-url", type=str, required=False, help="Database URL (e.g., sqlite:///ads.db).")
@click.option("--seed", type=int, required=False, help="Random seed for reproducible generation.")
def cmd_init_db(log_level: Optional[str] = None, db_url: Optional[str] = None, seed: Optional[int] = None) -> None:
    """Initialize a fresh database using the configured URL.

    Args:
        log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
        db_url (str, optional): Database URL such as "sqlite:///ads.db".
        seed (int, optional): Random seed for reproducibility when generating data.

    Returns:
        None

    Examples:
        CLI:
            $ python cli.py db init --db-url sqlite:///ads.db --log-level INFO --seed 42
    """
    # Local imports to avoid side-effects during docs build
    from db_utils import setup_env, init_db, get_logger

    setup_env(log_level, db_url, seed)
    init_db()
    get_logger(__name__).info("Initialized SQLite database")


@db.command("migrate")
@click.option("--log-level", type=str, required=False, help="Log verbosity (e.g., INFO, DEBUG).")
@click.option("--db-url", type=str, required=False, help="Database URL (e.g., sqlite:///ads.db).")
def cmd_migrate_db(log_level: Optional[str] = None, db_url: Optional[str] = None) -> None:
    """Apply database migrations for the current schema version.

    Args:
        log_level (str, optional): Log verbosity (e.g., "INFO", "DEBUG").
        db_url (str, optional): Database URL such as "sqlite:///ads.db".

    Returns:
        None

    Examples:
        CLI:
            $ python cli.py db migrate --db-url sqlite:///ads.db --log-level INFO
    """
    from db_utils import setup_env, migrate_db, get_logger

    setup_env(log_level, db_url)
    get_logger(__name__).info("Applying DB migrations")
    migrate_db()
    get_logger(__name__).info("Applied migrations")

# Expose callback aliases for Sphinx autodoc (API view)
cb_init_db = cmd_init_db.callback
cb_migrate_db = cmd_migrate_db.callback
