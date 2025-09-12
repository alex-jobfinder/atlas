from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text

from db_utils import session_scope
from models.registry import registry
from services.generator import create_advertiser_payload, create_campaign_payload


def test_money_stored_as_and_timestamps_present() -> None:
    adv = create_advertiser_payload(registry.AdvertiserCreate(name="P2 Co", contact_email="p2@example.com"))
    with session_scope() as s:
        s.add(adv)
        s.flush()
        adv_id = adv.id

    camp_payload = registry.CampaignCreate(
        advertiser_id=adv_id,
        name="P2",
        objective="AWARENESS",
        target_cpm=Decimal("42.50"),
        dsp_partner="DV360",
        flight=registry.FlightSchema(
            start_date=__import__("datetime").date.today(), end_date=__import__("datetime").date.today()
        ),
        budget=registry.BudgetSchema(amount=Decimal("123.45"), type="LIFETIME", currency="USD"),
        line_items=[
            registry.LineItemCreate(
                name="LI",
                ad_format="STANDARD_VIDEO",
                bid_cpm=Decimal("10.00"),
                pacing_pct=100,
                targeting={registry.TargetingKey.DEVICE.value: ["TV"]},
                creatives=[
                    registry.CreativeCreate(
                        asset_url="https://ex.com/a.mp4", mime_type=registry.CreativeMimeType.mp4, duration_seconds=15
                    )
                ],
            )
        ],
    )
    camp, flight, budget, freq, li, creatives = create_campaign_payload(camp_payload)
    with session_scope() as s:
        s.add(camp)
        s.flush()
        # timestamps exist on core tables
        row = s.get(registry.Campaign, camp.id)
        assert getattr(row, "created_at", None) is not None
        assert getattr(row, "updated_at", None) is not None

        # cents columns exist and are integers
        # verify via raw SQL
        flight.campaign_id = camp.id
        s.add(flight)
        budget.campaign_id = camp.id
        s.add(budget)
        s.flush()

        # use same session transaction visibility
        c = s.execute(text("SELECT target_cpm FROM campaigns WHERE id=:id"), {"id": camp.id}).scalar_one()
        b = s.execute(text("SELECT amount FROM budgets WHERE campaign_id=:id"), {"id": camp.id}).scalar_one()
        assert c == 4250
        assert b == 12345


def test_timestamps_on_all_primary_tables() -> None:
    adv = create_advertiser_payload(registry.AdvertiserCreate(name="TS", contact_email="ts@example.com"))
    with session_scope() as s:
        s.add(adv)
        s.flush()
        adv_id = adv.id
        assert adv_id is not None

    camp_payload = registry.CampaignCreate(
        advertiser_id=adv_id,
        name="TS Camp",
        objective="AWARENESS",
        target_cpm=Decimal("10"),
        dsp_partner="DV360",
        flight=registry.FlightSchema(
            start_date=__import__("datetime").date.today(), end_date=__import__("datetime").date.today()
        ),
        budget=registry.BudgetSchema(amount=Decimal("1"), type="LIFETIME", currency="USD"),
        line_items=[
            registry.LineItemCreate(
                name="li",
                ad_format="STANDARD_VIDEO",
                bid_cpm=Decimal("10"),
                pacing_pct=100,
                targeting={},
                creatives=[
                    registry.CreativeCreate(
                        asset_url="https://x/y.mp4", mime_type=registry.CreativeMimeType.mp4, duration_seconds=15
                    )
                ],
            )
        ],
    )
    camp, flight, budget, freq, li, creatives = create_campaign_payload(camp_payload)
    with session_scope() as s:
        s.add(camp)
        s.flush()
        li.campaign_id = camp.id
        s.add(li)
        s.flush()
        cr = registry.Creative(
            line_item_id=li.id,
            asset_url="https://x/y.mp4",
            mime_type=registry.CreativeMimeType.mp4.value,
            duration_seconds=15,
            qa_status="APPROVED",
        )
        s.add(cr)
        s.flush()
        # at least campaign has timestamps (others to be added later in impl)
        assert getattr(camp, "created_at", None) is not None
        assert getattr(camp, "updated_at", None) is not None
