from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True)


def test_config_env_overrides_db_url_and_logger_level(monkeypatch, tmp_path) -> None:
    db_file = tmp_path / "ads_p1.db"
    monkeypatch.setenv("ADS_DB_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    proc = _run(
        [
            sys.executable,
            "-c",
            "import db_utils; print(db_utils.get_settings().ADS_DB_URL); print(db_utils.get_logger().level)",
        ]
    )
    assert proc.returncode == 0, proc.stderr
    lines = proc.stdout.strip().splitlines()
    assert lines[0].endswith(str(db_file))
    # Python logging level for DEBUG is 10
    assert lines[1].strip() in {"10", "DEBUG"}


def test_cli_typer_json_and_exit_codes(monkeypatch, tmp_path) -> None:
    # Ensure DB starts fresh
    db_file = tmp_path / "ads_p1.db"
    monkeypatch.setenv("ADS_DB_URL", f"sqlite:///{db_file}")
    _ = _run([sys.executable, "cli.py", "init-db"])

    # create-advertiser returns JSON with advertiser_id
    proc_adv = _run([sys.executable, "cli.py", "create-advertiser", "--auto", "--log-level", "INFO"])
    assert proc_adv.returncode == 0, proc_adv.stderr
    data = json.loads(proc_adv.stdout)
    assert "advertiser_id" in data and isinstance(data["advertiser_id"], int)

    # create-campaign missing advertiser should return exit code 2 (validation error)
    proc_bad = _run([sys.executable, "cli.py", "create-campaign", "--advertiser-id", "999999", "--auto"])
    assert proc_bad.returncode == 2
    # validation error: omit --auto to force usage error -> exit code 2
    proc_val = _run([sys.executable, "cli.py", "create-campaign", "--advertiser-id", str(data["advertiser_id"])])
    assert proc_val.returncode == 2


def test_init_db_respects_ads_db_url_env(tmp_path, monkeypatch):
    db_file = tmp_path / "typer_cli.db"
    monkeypatch.setenv("ADS_DB_URL", f"sqlite:///{db_file}")
    proc = _run([sys.executable, "cli.py", "init-db"])
    assert proc.returncode == 0, proc.stderr
    from importlib import reload

    import db_utils as db_module

    reload(db_module)
    with db_module.engine.connect() as conn:
        tables = {r[0] for r in conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
        assert "advertisers" in tables and "campaigns" in tables


def test_cli_accepts_seed_flag(tmp_path, monkeypatch):
    db_file = tmp_path / "seed_cli.db"
    monkeypatch.setenv("ADS_DB_URL", f"sqlite:///{db_file}")
    _ = _run([sys.executable, "cli.py", "init-db"])
    # Seed should be accepted and command should succeed
    proc = _run([sys.executable, "cli.py", "create-advertiser", "--auto", "--seed", "123"])
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert "advertiser_id" in data
