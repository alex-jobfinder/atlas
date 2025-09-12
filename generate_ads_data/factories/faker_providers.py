"""
Faker providers to generate realistic advertisers, campaigns, and assets.

Recommended improvements:
- Add profile-based generators (awareness/consideration/conversion) to tune distributions.
- Parameterize randomness via settings (seed, locale) and expose via CLI flags.
- Validate generated data against schema constraints before returning.

# TODO:
- KW generation using; https://advertools.readthedocs.io/en/master/advertools.kw_generate.html
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, Literal, Tuple

from faker import Faker

from models.registry import registry


fake = Faker()


def seed_all(seed: int) -> None:
    random.seed(seed)
    try:
        fake.seed_instance(seed)
    except Exception:
        pass


def fake_advertiser() -> tuple[str, str, str | None, str | None]:
    name = fake.company()
    email = fake.company_email()
    brand = random.choice([None, fake.word().title()])
    agency = random.choice([None, fake.company()])
    return name, email, brand, agency


def fake_campaign_dates() -> Tuple[date, date]:
    # start = date.today() + timedelta(days=registry.CampaignDefaults.DEFAULT_CAMPAIGN_START_OFFSET_DAYS)
    # end = start + timedelta(
    #     days=random.randint(
    #         registry.CampaignDefaults.DEFAULT_CAMPAIGN_MIN_DURATION_DAYS,
    #         registry.CampaignDefaults.DEFAULT_CAMPAIGN_MAX_DURATION_DAYS,
    #     )
    # )
    # return start, end
    end = date.today()
    start = end - timedelta(
        days=random.randint(
            registry.CampaignDefaults.DEFAULT_CAMPAIGN_MIN_DURATION_DAYS,
            registry.CampaignDefaults.DEFAULT_CAMPAIGN_MAX_DURATION_DAYS,
        )
    )
    return start, end

def fake_budget_and_cpm() -> tuple[Decimal, str, Decimal]:
    # Clamp CPM within configured bounds, then quantize
    clamped = max(
        float(registry.PricingDefaults.DEFAULT_CPM_MIN),
        min(
            float(registry.PricingDefaults.DEFAULT_CPM_MAX),
            random.gauss(
                float(registry.PricingDefaults.DEFAULT_CPM_GAUSS_MEAN),
                float(registry.PricingDefaults.DEFAULT_CPM_GAUSS_STDDEV),
            ),
        ),
    )
    cpm = Decimal(str(clamped)).quantize(registry.BudgetDefaults.DECIMAL)
    amount = Decimal(
        random.randint(
            int(registry.BudgetDefaults.DEFAULT_BUDGET_MIN), int(registry.BudgetDefaults.DEFAULT_BUDGET_MAX)
        )
    ).quantize(registry.BudgetDefaults.DECIMAL)
    btype = random.choice([registry.BudgetType.lifetime.value, registry.BudgetType.daily.value])  # v1 supports both
    return amount, btype, cpm


def fake_line_item_name() -> str:
    return f"LI {fake.word().title()}"


def fake_asset() -> tuple[str, str, int]:
    url = fake.image_url(
        width=registry.CreativeDefaults.DEFAULT_IMAGE_WIDTH, height=registry.CreativeDefaults.DEFAULT_IMAGE_HEIGHT
    )
    return (
        url,
        registry.CreativeMimeType.mp4.value,
        random.choice(registry.CreativeDefaults.ALLOWED_CREATIVE_DURATIONS),
    )


def fake_targeting_v2() -> dict:
    return {
        registry.TargetingKey.DEVICE.value: [random.choice(["TV", "MOBILE", "DESKTOP", "TABLET"])],
        registry.TargetingKey.GEO_COUNTRY.value: [random.choice(["US", "CA", "GB", "DE"])],
        registry.TargetingKey.CONTENT_GENRE.value: [random.choice(["DRAMA", "COMEDY", "ACTION"])],
        registry.TargetingKey.AGE_RANGE.value: random.choice(
            [list(r) for r in registry.TargetingDefaults.DEFAULT_AGE_RANGES]
        ),
        registry.TargetingKey.GENDER.value: random.choice(["MALE", "FEMALE", "ALL"]),
        registry.TargetingKey.HOUSEHOLD_INCOME.value: random.choice(["LOW", "MID", "HIGH"]),
    }


# Profile-based generation (AWARENESS, CONSIDERATION, CONVERSION)
ProfileName = Literal["AWARENESS", "CONSIDERATION", "CONVERSION"]


def profile_tuned_cpm(profile: ProfileName) -> Decimal:
    # shift mean CPM per profile (now in USD, not cents)
    mean = {
        "AWARENESS": 25.00,
        "CONSIDERATION": 20.00,
        "CONVERSION": 18.00,
    }[profile]
    std = float(registry.PricingDefaults.DEFAULT_CPM_GAUSS_STDDEV)
    clamped = max(
        float(registry.PricingDefaults.DEFAULT_CPM_MIN),
        min(float(registry.PricingDefaults.DEFAULT_CPM_GAUSS_STDDEV), random.gauss(mean, std)),
    )
    return Decimal(str(clamped)).quantize(registry.BudgetDefaults.DECIMAL)


def profile_tuned_budget(profile: ProfileName) -> Decimal:
    low, high = {
        "AWARENESS": (80000, 150000),
        "CONSIDERATION": (30000, 80000),
        "CONVERSION": (10000, 40000),
    }[profile]
    return Decimal(random.randint(low, high)).quantize(registry.BudgetDefaults.DECIMAL)


def profile_tuned_duration(profile: ProfileName) -> int:
    if profile == "AWARENESS":
        return 30
    if profile == "CONSIDERATION":
        return random.choice([20, 15])
    return 15


def profile_tuned_targeting(profile: ProfileName) -> Dict[str, Any]:
    t = fake_targeting_v2()
    if profile == "AWARENESS":
        t[registry.TargetingKey.DEVICE.value] = ["TV"]
    elif profile == "CONVERSION":
        t[registry.TargetingKey.DEVICE.value] = ["MOBILE", "DESKTOP"]
    return t


def make_profile_creative(profile: ProfileName, asset_url: str | None = None) -> registry.CreativeCreate:
    url = asset_url or fake.image_url(
        width=registry.CreativeDefaults.DEFAULT_IMAGE_WIDTH, height=registry.CreativeDefaults.DEFAULT_IMAGE_HEIGHT
    )
    mime = registry.CreativeMimeType.mp4
    duration = profile_tuned_duration(profile)
    # Pre-validate with schema
    return registry.CreativeCreate(asset_url=url, mime_type=mime, duration_seconds=duration)
