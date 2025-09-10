from __future__ import annotations

from pydantic import BaseModel


class CampaignMetric(BaseModel):
    """Metrics for a single marketing campaign.

    Attributes
    ----------
    campaign_id: str
        Identifier for the campaign.
    impressions: int
        Number of impressions served.
    clicks: int
        Number of clicks received.
    spend: float
        Total advertising spend in USD.
    """

    campaign_id: str
    impressions: int
    clicks: int
    spend: float