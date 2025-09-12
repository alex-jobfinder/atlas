"""
Cross-field validators for campaign payloads.

Recommended improvements:
- Add warnings (not just hard errors) for soft constraints (e.g., budget typical minimums).
- Extend to validate targeting semantics (e.g., ranges, device constraints per format).
"""
from __future__ import annotations

from decimal import Decimal

from models.registry import registry


def validate_campaign_v1(payload: registry.CampaignCreate) -> None:
    if len(payload.line_items) != 1:
        raise ValueError("v1 requires exactly 1 line item")

    if payload.flight.end_date < payload.flight.start_date:
        raise ValueError("end_date must be >= start_date")

    min_cpm = registry.PricingDefaults.DEFAULT_CPM_MIN
    max_cpm = registry.PricingDefaults.DEFAULT_CPM_MAX
    if not (Decimal(min_cpm) <= payload.target_cpm <= Decimal(max_cpm)):
        raise ValueError(f"target_cpm must be between {min_cpm} and {max_cpm}")
