from __future__ import annotations

from decimal import Decimal

import pytest

from models.registry import registry


def test_adformat_enum_includes_v2_values() -> None:
    assert registry.AdFormat.binge_ads.value == "BINGE_ADS"
    assert registry.AdFormat.pause_ads.value == "PAUSE_ADS"
    assert registry.AdFormat.interactive_overlay.value == "INTERACTIVE_OVERLAY"
    assert registry.AdFormat.sponsorship.value == "SPONSORSHIP"
    assert registry.AdFormat.standard_video.value == "STANDARD_VIDEO"


def test_line_item_targeting_whitelist_accepts_known_keys() -> None:
    li = registry.LineItemCreate(
        name="LI V2",
        ad_format=registry.AdFormat.standard_video,
        bid_cpm=Decimal("50.00"),
        pacing_pct=100,
        targeting={
            registry.TargetingKey.DEVICE.value: ["TV"],
            registry.TargetingKey.GEO_COUNTRY.value: ["US"],
            registry.TargetingKey.CONTENT_GENRE.value: ["DRAMA"],
            registry.TargetingKey.AGE_RANGE.value: [25, 34],
            registry.TargetingKey.GENDER.value: "ALL",
            registry.TargetingKey.HOUSEHOLD_INCOME.value: "MID",
        },
        creatives=[
            registry.CreativeCreate(
                asset_url="https://example.com/ad.mp4", mime_type=registry.CreativeMimeType.mp4, duration_seconds=15
            )
        ],
    )
    assert li.targeting[registry.TargetingKey.DEVICE.value] == ["TV"]


def test_line_item_targeting_whitelist_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError):
        registry.LineItemCreate(
            name="LI Bad",
            ad_format=registry.AdFormat.standard_video,
            bid_cpm=Decimal("55.00"),
            pacing_pct=100,
            targeting={"unknown_key": True},
            creatives=[
                registry.CreativeCreate(
                    asset_url="https://example.com/ad.mp4",
                    mime_type=registry.CreativeMimeType.mp4,
                    duration_seconds=15,
                )
            ],
        )
