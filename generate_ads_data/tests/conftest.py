from __future__ import annotations

import importlib

import pytest


@pytest.fixture(autouse=True)
def _isolation(tmp_path, monkeypatch):
    # Point to a temp SQLite DB for tests that don't override
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("ADS_DB_URL", f"sqlite:///{db_path}")
    import db_utils as db_module

    importlib.reload(db_module)
    db_module.init_db()
    yield
