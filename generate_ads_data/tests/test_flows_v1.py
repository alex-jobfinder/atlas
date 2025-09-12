from __future__ import annotations

from decimal import Decimal

from db_utils import session_scope
from models.registry import registry
from services.generator import create_advertiser_payload, create_campaign_payload
from services.validators import validate_campaign_v1


def test_create_advertiser_and_campaign_v1() -> None:
    adv_payload = registry.AdvertiserCreate(name="Acme Inc", contact_email="ads@acme.com")
    advertiser = create_advertiser_payload(adv_payload)
    with session_scope() as s:
        s.add(advertiser)
        s.flush()
        adv_id = advertiser.id

    camp_payload = registry.CampaignCreate(
        advertiser_id=adv_id,
        name="Spring Awareness",
        objective="AWARENESS",
        target_cpm=Decimal("35.00"),
        dsp_partner="DV360",
        flight=registry.FlightSchema(
            start_date=__import__("datetime").date.today(), end_date=__import__("datetime").date.today()
        ),
        budget=registry.BudgetSchema(amount=Decimal("10000.00"), type="LIFETIME", currency="USD"),
        line_items=[
            registry.LineItemCreate(
                name="Default LI",
                ad_format="STANDARD_VIDEO",
                bid_cpm=Decimal("35.00"),
                pacing_pct=100,
                targeting={registry.TargetingKey.DEVICE.value: ["TV"]},
                creatives=[
                    registry.CreativeCreate(
                        asset_url="https://example.com/ad.mp4",
                        mime_type=registry.CreativeMimeType.mp4,
                        duration_seconds=15,
                    )
                ],
            )
        ],
    )

    validate_campaign_v1(camp_payload)
    camp, flight, budget, freq, li, creatives = create_campaign_payload(camp_payload)
    with session_scope() as s:
        s.add(camp)
        s.flush()
        flight.campaign_id = camp.id
        budget.campaign_id = camp.id
        s.add(flight)
        s.add(budget)
        s.flush()
        li.campaign_id = camp.id
        s.add(li)
        s.flush()
        for cr in creatives:
            s.add(
                registry.Creative(
                    line_item_id=li.id,
                    asset_url=cr.asset_url,
                    mime_type=cr.mime_type,
                    duration_seconds=int(cr.duration_seconds),
                    qa_status="APPROVED",
                )
            )
        s.flush()

        assert s.get(registry.Advertiser, adv_id) is not None
        assert s.get(registry.Campaign, camp.id) is not None
        assert s.query(registry.Flight).filter_by(campaign_id=camp.id).count() == 1
        assert s.query(registry.Budget).filter_by(campaign_id=camp.id).count() == 1
