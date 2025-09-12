from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import select

from db_utils import session_scope
from models.registry import registry
from services.generator import create_advertiser_payload, create_campaign_payload
from services.performance import generate_hourly_performance


def test_performance_metrics_generation() -> None:
    """Test that all performance metrics are generated with realistic values."""
    # Create test campaign
    adv = create_advertiser_payload(registry.AdvertiserCreate(name="Test Co", contact_email="test@example.com"))
    with session_scope() as s:
        s.add(adv)
        s.flush()
        adv_id = adv.id

    camp_payload = registry.CampaignCreate(
        advertiser_id=adv_id,
        name="Test Campaign",
        objective="AWARENESS",
        target_cpm=Decimal("25.00"),
        dsp_partner="DV360",
        flight=registry.FlightSchema(start_date=date(2024, 1, 1), end_date=date(2024, 1, 1)),  # 1 day = 24 hours
        budget=registry.BudgetSchema(amount=Decimal("1000.00"), type="LIFETIME", currency="USD"),
        line_items=[
            registry.LineItemCreate(
                name="Test LI",
                ad_format="STANDARD_VIDEO",
                bid_cpm=Decimal("20.00"),
                pacing_pct=100,
                targeting={},
                creatives=[
                    registry.CreativeCreate(
                        asset_url="https://test.com/video.mp4",
                        mime_type=registry.enums.CreativeMimeType.mp4,
                        duration_seconds=30,
                    )
                ],
            )
        ],
    )
    camp, flight, budget, freq, li, creatives = create_campaign_payload(camp_payload)

    with session_scope() as s:
        s.add(camp)
        s.flush()  # Flush campaign first to get its ID

        # Now set the campaign_id on related objects
        flight.campaign_id = camp.id
        budget.campaign_id = camp.id
        li.campaign_id = camp.id

        s.add(flight)
        s.add(budget)
        s.add(li)
        s.flush()

        # Create actual Creative ORM objects
        for cr_schema in creatives:
            cr = registry.Creative(
                line_item_id=li.id,
                asset_url=cr_schema.asset_url,
                mime_type=cr_schema.mime_type.value,
                duration_seconds=cr_schema.duration_seconds,
                qa_status="APPROVED",
            )
            s.add(cr)
        s.flush()

        # Commit all data so it's visible to the performance generation function
        s.commit()

        # Generate performance data
        rows_generated = generate_hourly_performance(camp.id, seed=42, replace=True)
        assert rows_generated == 24  # 24 hours from 2024-01-01 (1-day flight)

        # Verify all metrics are present and realistic
        perf_rows = (
            s.execute(select(registry.CampaignPerformance).where(registry.CampaignPerformance.campaign_id == camp.id))
            .scalars()
            .all()
        )
        assert len(perf_rows) == 24

        for perf in perf_rows:
            # Check that all required fields are present
            assert perf.impressions > 0
            assert perf.clicks >= 0
            assert 0.0 <= perf.ctr <= 0.05  # CTR should be 0-5%
            assert 0 <= perf.completion_rate <= 1  # Completion rate should be 0-1 ratio
            assert 0.0 <= perf.render_rate <= 1.0
            assert 0.0 <= perf.fill_rate <= 1.0
            assert 0.0 <= perf.response_rate <= 1.0
            assert 0.0 <= perf.video_skip_rate <= 1.0
            assert perf.video_start >= 0
            assert perf.frequency >= 1
            assert perf.reach > 0

            # Verify CTR calculation
            if perf.impressions > 0:
                expected_ctr = perf.clicks / perf.impressions
                assert abs(float(perf.ctr) - expected_ctr) < 0.001  # Increased tolerance for precision issues

            # Verify video start is reasonable (should be high percentage of impressions)
            assert perf.video_start <= perf.impressions
            if perf.impressions > 0:
                start_rate = perf.video_start / perf.impressions
                assert 0.7 <= start_rate <= 0.99  # 70-99% of impressions should start video

            # Verify completion rate is ratio (0-1)
            assert 0 <= perf.completion_rate <= 1

            # Verify frequency and reach relationship
            assert perf.frequency >= 1
            assert perf.reach >= 1
            if perf.frequency > 1:
                assert perf.reach <= perf.impressions


def test_performance_metrics_realistic_ranges() -> None:
    """Test that performance metrics fall within realistic industry ranges."""
    # Create test campaign
    adv = create_advertiser_payload(registry.AdvertiserCreate(name="Range Test Co", contact_email="range@example.com"))
    with session_scope() as s:
        s.add(adv)
        s.flush()
        adv_id = adv.id

    camp_payload = registry.CampaignCreate(
        advertiser_id=adv_id,
        name="Range Test Campaign",
        objective="CONSIDERATION",
        target_cpm=Decimal("35.00"),
        dsp_partner="DV360",
        flight=registry.FlightSchema(start_date=date(2024, 1, 1), end_date=date(2024, 1, 1)),  # 1 day = 24 hours
        budget=registry.BudgetSchema(amount=Decimal("500.00"), type="LIFETIME", currency="USD"),
        line_items=[
            registry.LineItemCreate(
                name="Range Test LI",
                ad_format="STANDARD_VIDEO",
                bid_cpm=Decimal("30.00"),
                pacing_pct=100,
                targeting={},
                creatives=[
                    registry.CreativeCreate(
                        asset_url="https://test.com/video.mp4",
                        mime_type=registry.enums.CreativeMimeType.mp4,
                        duration_seconds=15,
                    )
                ],
            )
        ],
    )
    camp, flight, budget, freq, li, creatives = create_campaign_payload(camp_payload)

    with session_scope() as s:
        s.add(camp)
        s.flush()  # Flush campaign first to get its ID

        # Now set the campaign_id on related objects
        flight.campaign_id = camp.id
        budget.campaign_id = camp.id
        li.campaign_id = camp.id

        s.add(flight)
        s.add(budget)
        s.add(li)
        s.flush()

        # Create actual Creative ORM objects
        for cr_schema in creatives:
            cr = registry.Creative(
                line_item_id=li.id,
                asset_url=cr_schema.asset_url,
                mime_type=cr_schema.mime_type.value,
                duration_seconds=cr_schema.duration_seconds,
                qa_status="APPROVED",
            )
            s.add(cr)
        s.flush()

        # Commit all data so it's visible to the performance generation function
        s.commit()

        # Generate performance data
        generate_hourly_performance(camp.id, seed=123, replace=True)

        # Check realistic ranges across all hours
        perf_rows = (
            s.execute(select(registry.CampaignPerformance).where(registry.CampaignPerformance.campaign_id == camp.id))
            .scalars()
            .all()
        )

        for perf in perf_rows:
            # Industry standard ranges
            assert Decimal("0.0001") <= perf.ctr <= Decimal("0.05"), f"CTR {perf.ctr} outside realistic range"
            assert (
                Decimal("0.90") <= perf.render_rate <= Decimal("0.999")
            ), f"Render rate {perf.render_rate} outside realistic range"
            assert (
                Decimal("0.80") <= perf.fill_rate <= Decimal("0.999")
            ), f"Fill rate {perf.fill_rate} outside realistic range"
            assert (
                Decimal("0.001") <= perf.response_rate <= Decimal("0.10")
            ), f"Response rate {perf.response_rate} outside realistic range"
            assert (
                Decimal("0.05") <= perf.video_skip_rate <= Decimal("0.60")
            ), f"Video skip rate {perf.video_skip_rate} outside realistic range"

            # Video start should be high percentage of impressions
            if perf.impressions > 0:
                start_rate = perf.video_start / perf.impressions
                assert (
                    Decimal("0.70") <= Decimal(str(start_rate)) <= Decimal("0.99")
                ), f"Video start rate {start_rate} outside realistic range"
