from __future__ import annotations

from pathlib import Path

import click
import pytest


def test_cli_registry_has_db_init() -> None:
    """Verify grouped CLI exposes 'db init' and its docstring."""
    from cli import cli as root

    root_ctx = click.Context(root)
    root_commands = root.list_commands(root_ctx)
    assert "db" in root_commands, "'db' group should be registered on the root CLI"

    db_group = root.get_command(root_ctx, "db")
    assert isinstance(db_group, click.core.Group)

    db_ctx = click.Context(db_group)
    db_commands = db_group.list_commands(db_ctx)
    assert "init" in db_commands, "'init' should be registered under 'db' group"

    cmd = db_group.get_command(db_ctx, "init")
    assert cmd is not None, "Click command object for 'db init' not found"
    # The underlying callback docstring should still be descriptive
    assert cmd.callback.__doc__ and "Initialize a fresh database" in cmd.callback.__doc__


def test_docs_smoke_build_cli_pages(tmp_path: Path) -> None:
    """Build docs and ensure CLI pages are generated (smoke test only)."""
    pytest.importorskip("sphinx")
    pytest.importorskip("sphinx_click")
    from sphinx.cmd.build import main as sphinx_build_main  # type: ignore

    repo_root = Path(__file__).resolve().parents[1]
    docs_src = repo_root / "docs"
    outdir = tmp_path / "html"

    rc = sphinx_build_main(["-b", "html", "-q", str(docs_src), str(outdir)])
    assert rc == 0, "Sphinx build failed"

    # Ensure both API and CLI pages exist
    assert (outdir / "api" / "cli.html").exists()
    assert (outdir / "cli_commands.html").exists()
