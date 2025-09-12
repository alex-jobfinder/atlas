"""
Database utilities: settings, logger, SQLAlchemy engine/session helpers.

Recommended improvements:
- Add structured JSON logging and per-request context (e.g., campaign_id) when applicable.
- Support multiple databases/environments via profiles; expose pool settings.
- Consider Alembic migrations if schema evolves beyond simple resets.
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import sessionmaker

from models.registry import registry


try:
    from colorlog import ColoredFormatter  # type: ignore
except Exception:
    ColoredFormatter = None  # type: ignore


@dataclass(frozen=True)
class Settings:
    ADS_DB_URL: str = os.getenv("ADS_DB_URL", "sqlite:///./ads.db")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


def get_settings() -> Settings:
    return Settings()


def get_logger(name: str = "ads") -> logging.Logger:
    logger = logging.getLogger(name)
    level_name = os.getenv("LOG_LEVEL", get_settings().LOG_LEVEL).upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        if ColoredFormatter is not None:
            fmt = ColoredFormatter(
                "%(log_color)s%(asctime)s %(levelname)s %(name)s - %(message)s",
                reset=True,
                log_colors={
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
            )
        else:
            fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


# Database engine and session setup use the configured DB URL
DB_URL = get_settings().ADS_DB_URL
engine = create_engine(DB_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    with engine.connect() as conn:
        if DB_URL.startswith("sqlite"):
            conn.execute(text("PRAGMA foreign_keys=ON"))
            conn.execute(text("PRAGMA journal_mode=WAL"))

    registry.Base.metadata.drop_all(bind=engine)
    registry.Base.metadata.create_all(bind=engine)

    # Create the campaign hierarchy view
    create_campaign_hierarchy_view()


def migrate_db() -> None:
    """
    Lightweight, Alembic-style migration shim for SQLite.

    Applies incremental changes without dropping data:
    - Add creatives.checksum column (nullable, TEXT/STRING)
    - Create ix_campaign_status_created index on campaigns(status, created_at)
    - Add new performance metrics columns to campaign_performance table

    Safe to run multiple times (idempotent checks).
    """
    with engine.begin() as conn:
        # 1) Add creatives.checksum if missing
        try:
            cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info('creatives')").fetchall()]
            if "checksum" not in cols:
                conn.exec_driver_sql("ALTER TABLE creatives ADD COLUMN checksum TEXT")
        except Exception:
            # Table might not exist yet; skip gracefully
            pass

        # 2) Create composite index on campaigns(status, created_at) if missing
        try:
            idx_rows = conn.exec_driver_sql("PRAGMA index_list('campaigns')").fetchall()
            idx_names = {r[1] for r in idx_rows}  # r[1] = name
            if "ix_campaign_status_created" not in idx_names:
                conn.exec_driver_sql("CREATE INDEX ix_campaign_status_created ON campaigns(status, created_at)")
        except Exception:
            pass

        # 3) Add new performance metrics columns to campaign_performance if missing
        try:
            perf_cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info('campaign_performance')").fetchall()]
            new_columns = [
                ("clicks", "INTEGER NOT NULL DEFAULT 0"),
                ("ctr", "NUMERIC(5,4) NOT NULL DEFAULT 0.0"),
                ("render_rate", "NUMERIC(5,4) NOT NULL DEFAULT 0.0"),
                ("fill_rate", "NUMERIC(5,4) NOT NULL DEFAULT 0.0"),
                ("response_rate", "NUMERIC(5,4) NOT NULL DEFAULT 0.0"),
                ("video_skip_rate", "NUMERIC(5,4) NOT NULL DEFAULT 0.0"),
                ("video_start", "INTEGER NOT NULL DEFAULT 0"),
            ]

            for col_name, col_def in new_columns:
                if col_name not in perf_cols:
                    conn.exec_driver_sql(f"ALTER TABLE campaign_performance ADD COLUMN {col_name} {col_def}")
        except Exception:
            # Table might not exist yet; skip gracefully
            pass


@contextmanager
def session_scope() -> Iterator:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------- Helper methods moved from cli.py ----------


def setup_env(log_level: str | None = None, db_url: str | None = None, seed: int | None = None) -> None:
    """Set common environment knobs for CLI commands."""
    if log_level:
        os.environ["LOG_LEVEL"] = log_level
    if db_url:
        os.environ["ADS_DB_URL"] = db_url
    if seed is not None:
        from factories.faker_providers import seed_all as faker_seed_all

        faker_seed_all(seed)


def safe_load_yaml(path: str) -> dict[str, any]:
    """Load a YAML file and ensure the root is a mapping."""
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required: pip install pyyaml")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError("YAML root must be a mapping (dict)")
        return data
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {path}")
    except Exception as e:
        raise Exception(f"Failed to parse YAML: {e}")


def parse_date(value: any) -> str:
    """Coerce either a date or YYYY-MM-DD string into a date object."""
    from datetime import date

    if isinstance(value, date):
        return value
    if isinstance(value, str) and len(value.split("-")) == 3:
        try:
            y, m, d = map(int, value.split("-"))
            return date(y, m, d)
        except ValueError:
            pass
    raise ValueError(f"Invalid date: {value!r} (expected YYYY-MM-DD)")


def coerce_creative(c: dict[str, any]) -> any:
    """Convert a loosely-typed creative dict into a CreativeCreate schema."""
    from models.registry import registry

    return registry.CreativeCreate(
        asset_url=c.get("asset_url", "https://example.com/ad.mp4"),
        mime_type=c.get("mime_type", "VIDEO/MP4"),
        duration_seconds=int(c.get("duration_seconds", 15)),
    )


def build_auto_campaign(advertiser_id: int | None, profile: str | None) -> any:
    """Build a single demo campaign payload for an advertiser."""
    import random
    from decimal import Decimal

    from factories.faker_providers import (
        fake_asset,
        fake_budget_and_cpm,
        fake_campaign_dates,
        fake_line_item_name,
        fake_targeting_v2,
        make_profile_creative,
        profile_tuned_budget,
        profile_tuned_cpm,
        profile_tuned_targeting,
    )
    from models.registry import registry

    start, end = fake_campaign_dates()

    if profile:
        amount, cpm = profile_tuned_budget(profile), profile_tuned_cpm(profile)
        btype = random.choice([registry.BudgetType.lifetime.value, registry.BudgetType.daily.value])
        targeting, creative = profile_tuned_targeting(profile), make_profile_creative(profile)
        objective = "AWARENESS"
    else:
        amount, btype, cpm = fake_budget_and_cpm()
        targeting = fake_targeting_v2()
        asset_url, mime, dur = fake_asset()
        creative = registry.CreativeCreate(asset_url=asset_url, mime_type=mime, duration_seconds=dur)
        objective = "AWARENESS"

    return registry.CampaignCreate(
        advertiser_id=advertiser_id,
        name=f"Campaign {fake_line_item_name()}",
        objective=objective,
        status="ACTIVE",
        target_cpm=Decimal(str(cpm)),
        dsp_partner="DV360",
        flight=registry.FlightSchema(start_date=start, end_date=end),
        budget=registry.BudgetSchema(amount=Decimal(str(amount)), type=btype, currency="USD"),
        line_items=[
            registry.LineItemCreate(
                name=fake_line_item_name(),
                ad_format="STANDARD_VIDEO",
                bid_cpm=Decimal(str(cpm)),
                pacing_pct=100,
                targeting=targeting,
                creatives=[creative],
            )
        ],
    )


# db_utils.py (or a new utils module)


def persist_advertiser(payload: any) -> int:
    """Get-or-create an advertiser by unique contact_email; return its id."""

    from services.generator import create_advertiser_payload

    with session_scope() as s:
        existing = s.execute(
            select(registry.Advertiser).where(registry.Advertiser.contact_email == payload.contact_email)
        ).scalar_one_or_none()

        if existing:
            return existing.id

        adv = create_advertiser_payload(payload)
        s.add(adv)
        s.flush()
        s.refresh(adv)
        return adv.id


def persist_campaign(advertiser_id: int | None, payload: any, return_ids: bool = False) -> dict[str, any]:
    """Validate and persist a campaign and its children."""

    from services.generator import create_campaign_payload
    from services.validators import validate_campaign_v1

    if advertiser_id is None:
        print(json.dumps({"error": "advertiser_id is required"}))
        raise SystemExit(4)

    try:
        validate_campaign_v1(payload)
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        raise SystemExit(2)

    with session_scope() as s:
        # Verify advertiser exists
        if not s.execute(
            select(registry.Advertiser).where(registry.Advertiser.id == advertiser_id)
        ).scalar_one_or_none():
            print(json.dumps({"error": f"Advertiser with id {advertiser_id} not found"}))
            raise SystemExit(2)

        # Create campaign objects
        camp, flight, budget, freq, line_item, creatives = create_campaign_payload(payload)
        camp.advertiser_id = advertiser_id

        # Persist campaign hierarchy
        s.add(camp)
        s.flush()

        for obj in [flight, budget, line_item]:
            obj.campaign_id = camp.id
            s.add(obj)

        if freq:
            freq.campaign_id = camp.id
            s.add(freq)

        s.flush()

        # Add creatives
        for cr in creatives:
            s.add(
                registry.Creative(
                    line_item_id=line_item.id,
                    asset_url=cr.asset_url,
                    mime_type=cr.mime_type,
                    duration_seconds=int(cr.duration_seconds),
                    qa_status=registry.QAStatus.approved.value,
                )
            )

        s.flush()
        result = {"campaign_id": camp.id, "line_item_id": line_item.id}

        if return_ids:
            result["advertiser_id"] = advertiser_id

        print(json.dumps(result))
        return result


def generate_hourly_performance(campaign_id: int, seed: int | None = None, replace: bool = True) -> int:
    """Generate synthetic hourly performance rows for a campaign."""
    from services.performance import generate_hourly_performance as _generate_hourly_performance

    return _generate_hourly_performance(campaign_id, seed=seed, replace=replace)


def generate_performance(campaign_id: int, seed: int | None = None, replace: bool = True) -> dict[str, any]:
    """Generate synthetic hourly performance rows for a campaign and return summary."""
    rows = generate_hourly_performance(campaign_id, seed=seed, replace=replace)
    return {"campaign_id": campaign_id, "rows": rows}


def create_campaign_hierarchy_view() -> None:
    """Create the campaign hierarchy view for analytics."""
    view_sql = """
    CREATE VIEW IF NOT EXISTS v_campaign_hierarchy AS
    SELECT
        -- Primary key columns
        c.id as creative_id,
        li.id as line_item_id,
        camp.id as campaign_id,
        adv.id as advertiser_id,

        -- Advertiser columns (highest level)
        adv.name as advertiser_name,
        adv.status as advertiser_status,
        adv.created_at as advertiser_created_at,
        adv.updated_at as advertiser_updated_at,
        adv.brand,
        adv.contact_email,
        adv.agency_name,

        -- Campaign columns
        camp.name as campaign_name,
        camp.status as campaign_status,
        camp.created_at as campaign_created_at,
        camp.updated_at as campaign_updated_at,
        camp.objective,
        camp.currency,
        camp.target_cpm,
        camp.dsp_partner,
        camp.programmatic_buy_type,
        camp.programmatic_partner,
        camp.content_adjacency_tier,
        camp.brand_lift_enabled,
        camp.attention_metrics_enabled,
        camp.clean_room_provider,
        camp.measurement_partner,
        camp.external_ref,

        -- Flight columns
        f.id as flight_id,
        f.start_date,
        f.end_date,
        f.created_at as flight_created_at,
        f.updated_at as flight_updated_at,

        -- Budget columns
        b.id as budget_id,
        b.amount,
        b.type as budget_type,
        b.currency as budget_currency,
        b.created_at as budget_created_at,
        b.updated_at as budget_updated_at,

        -- Line Item columns
        li.name as line_item_name,
        li.status as line_item_status,
        li.created_at as line_item_created_at,
        li.updated_at as line_item_updated_at,
        li.ad_format,
        li.bid_cpm,
        li.pacing_pct,
        li.targeting_json,
        li.device_targets_json,
        li.duration_seconds as line_item_duration_seconds,
        li.ad_server_type,
        li.pixel_vendor,
        li.geo_tier,

        -- Creative (Ad) columns (lowest level)
        c.name as creative_name,
        c.status as creative_status,
        c.created_at as creative_created_at,
        c.updated_at as creative_updated_at,
        c.asset_url,
        c.mime_type,
        c.duration_seconds,
        c.qa_status,
        c.placement,
        c.file_format,
        c.width,
        c.height,
        c.frame_rate,
        c.bitrate_kbps,
        c.file_size_bytes,
        c.is_interactive,
        c.interactive_meta_json,
        c.is_pause_ad,
        c.qr_code_url,
        c.overlay_cta_text

    FROM advertisers adv
    JOIN campaigns camp ON adv.id = camp.advertiser_id
    JOIN flights f ON camp.id = f.campaign_id
    JOIN budgets b ON camp.id = b.campaign_id
    JOIN line_items li ON camp.id = li.campaign_id
    JOIN creatives c ON li.id = c.line_item_id
    ORDER BY adv.id, camp.id, f.id, b.id, li.id, c.id;
    """

    with engine.connect() as conn:
        try:
            conn.execute(text(view_sql))
            conn.commit()
            print("✅ Campaign hierarchy view created successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not create campaign hierarchy view: {e}")
            # Continue anyway - this is not critical
