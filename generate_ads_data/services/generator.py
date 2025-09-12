"""
Campaign creation utilities for the Netflix Ads domain.

Recommended improvements:
- Add idempotency helpers (e.g., external_ref) to avoid duplicate inserts.
- Validate that mapped enum strings match schema expectations consistently.
- Consider splitting write paths for unit testing (pure mapping vs DB persistence).
"""
from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from models.registry import registry


def _q2(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _to(value: Decimal) -> int:
    return int((_q2(value) * 100).to_integral_value())


def create_advertiser_payload(data: registry.AdvertiserCreate) -> registry.Advertiser:
    adv = registry.Advertiser(
        name=data.name,
        brand=data.brand,
        contact_email=str(data.contact_email),
        agency_name=data.agency_name,
    )
    return adv


def _create_line_item(parent_campaign_id: int, li: registry.LineItemCreate) -> registry.LineItem:
    line_item = registry.LineItem(
        campaign_id=parent_campaign_id,
        name=li.name,
        ad_format=li.ad_format,
        bid_cpm=_to(li.bid_cpm),
        pacing_pct=int(li.pacing_pct),
        targeting_json=json.dumps(li.targeting),
    )
    return line_item


def _map_campaign_status_to_entity(status: object) -> str:
    try:
        value = getattr(status, "value", str(status))
        return registry.EntityStatusStr.ACTIVE.value if value == "ACTIVE" else registry.EntityStatusStr.INACTIVE.value
    except Exception:
        return registry.EntityStatusStr.INACTIVE.value


def create_campaign_payload(
    data: registry.CampaignCreate,
) -> tuple[
    registry.Campaign,
    registry.Flight,
    registry.Budget,
    Optional[registry.FrequencyCap],
    registry.LineItem,
    list[registry.CreativeCreate],
]:
    camp = registry.Campaign(
        advertiser_id=int(data.advertiser_id) if data.advertiser_id is not None else 0,
        name=data.name,
        objective=data.objective,
        status=_map_campaign_status_to_entity(data.status),
        currency=data.currency,
        target_cpm=_to(data.target_cpm),
        dsp_partner=data.dsp_partner,
    )
    flight = registry.Flight(
        campaign_id=0,  # set after camp id
        start_date=data.flight.start_date,
        end_date=data.flight.end_date,
    )
    budget = registry.Budget(
        campaign_id=0,  # set after camp id
        amount=_to(data.budget.amount),
        type=data.budget.type,
        currency=data.budget.currency,
    )
    freq: Optional[registry.FrequencyCap] = None
    if data.frequency_cap is not None:
        freq = registry.FrequencyCap(
            campaign_id=0,  # set after camp id
            count=int(data.frequency_cap.count),
            unit=data.frequency_cap.unit,
            scope=data.frequency_cap.scope,
        )

    # v1 constraint: exactly one line item
    li = data.line_items[0]
    line_item = _create_line_item(0, li)  # set FK after insert

    return camp, flight, budget, freq, line_item, li.creatives
