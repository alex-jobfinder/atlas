# performance_ext.py
from __future__ import annotations

from datetime import datetime, date, timedelta
from typing import Optional

from pydantic import BaseModel, computed_field
from sqlalchemy import select

from db_utils import session_scope
from models.registry import registry
from services.performance_utils import safe_div


"""
Extended performance generation with Pydantic models for calculated fields.

This module extends the basic performance data with Pydantic models that compute
derived metrics from raw data. It does NOT generate new data - it only adds
calculated fields to existing performance data.

NETFLIX CORE ADVERTISING METRICS (as documented by Netflix):
- Impressions: Total ad impressions served
- Clicks: Total click-through interactions
- CTR: Click-through rate (clicks/impressions)
- Video Completion Rate: Percentage of video ads completed
- Render Rate: Percentage of ads that rendered successfully
- Fill Rate: Percentage of ad requests that were filled
- Response Rate: Interactive engagement rate
- Video Skip Rate: Percentage of video ads skipped
- Video Start: Number of video ads that began playing

Design:
- NO data generation - uses existing performance data
- Pydantic computed fields for all derived metrics
- Adds calculated fields to existing performance rows
- Follows Netflix's documented metric definitions and ranges.
"""


class ExtendedPerformanceMetrics(BaseModel):
    """Extended performance metrics with calculated fields computed from raw data."""

    # Raw data fields (from basic performance)
    campaign_id: int
    hour_ts: datetime
    impressions: int
    clicks: int
    video_start: int
    frequency: int
    reach: int
    audience_json: Optional[str]

    # Extended raw fields (from basic performance)
    requests: int
    responses: int
    eligible_impressions: int
    auctions_won: int
    viewable_impressions: int
    audible_impressions: int
    video_q25: int
    video_q50: int
    video_q75: int
    video_q100: int
    skips: int
    qr_scans: int
    interactive_engagements: int
    spend: int
    error_count: int
    timeout_count: int

    # Temporal fields
    human_readable: str
    hour_of_day: int
    minute_of_hour: int
    second_of_minute: int
    day_of_week: int
    is_business_hour: bool

    # Date aggregation fields
    daily_day_date: date
    weekly_start_day_date: date
    monthly_start_day_date: date

    model_config = {"arbitrary_types_allowed": True}

    @computed_field
    @property
    def fill_rate_ext(self) -> float:
        """Percentage of ad requests that were filled."""
        return safe_div(self.eligible_impressions, self.requests)

    @computed_field
    @property
    def viewability_rate(self) -> float:
        """Percentage of impressions that were viewable."""
        return safe_div(self.viewable_impressions, self.impressions)

    @computed_field
    @property
    def audibility_rate(self) -> float:
        """Percentage of impressions that were audible."""
        return safe_div(self.audible_impressions, self.impressions)

    @computed_field
    @property
    def video_start_rate(self) -> float:
        """Percentage of impressions that started video playback."""
        return safe_div(self.video_start, self.impressions)

    @computed_field
    @property
    def video_completion_rate(self) -> float:
        """Percentage of video starts that completed (via q100)."""
        return safe_div(self.video_q100, self.video_start)

    @computed_field
    @property
    def video_skip_rate_ext(self) -> float:
        """Percentage of video starts that were skipped."""
        return safe_div(self.skips, self.video_start)

    @computed_field
    @property
    def qr_scan_rate(self) -> float:
        """QR scan rate."""
        return safe_div(self.qr_scans, self.impressions)

    @computed_field
    @property
    def interactive_rate(self) -> float:
        """Interactive engagement rate."""
        return safe_div(self.interactive_engagements, self.impressions)

    @computed_field
    @property
    def effective_cpm(self) -> int:
        """Effective CPM in cents."""
        return int(safe_div(self.spend * 1000, self.impressions))

    @computed_field
    @property
    def avg_watch_time_seconds(self) -> float:
        """Average watch time in seconds (estimated from quartiles)."""
        if self.video_start <= 0:
            return 0.0

        # Estimate from quartile data
        asset_seconds = 30  # Assume typical 30s assets

        # Calculate weighted average from quartile segments
        seg0 = max(0, self.video_start - self.video_q25)  # 0-25%
        seg1 = max(0, self.video_q25 - self.video_q50)  # 25-50%
        seg2 = max(0, self.video_q50 - self.video_q75)  # 50-75%
        seg3 = max(0, self.video_q75 - self.video_q100)  # 75-100%
        seg4 = max(0, self.video_q100)  # 100%

        # Midpoints for segments
        m0 = asset_seconds * 0.125
        m1 = asset_seconds * 0.375
        m2 = asset_seconds * 0.625
        m3 = asset_seconds * 0.875
        m4 = asset_seconds * 1.00

        total_watch = seg0 * m0 + seg1 * m1 + seg2 * m2 + seg3 * m3 + seg4 * m4
        return safe_div(total_watch, self.video_start)

    @computed_field
    @property
    def supply_funnel_efficiency(self) -> float:
        """Efficiency of supply funnel (eligible/requests)."""
        return safe_div(self.eligible_impressions, self.requests)

    @computed_field
    @property
    def auction_win_rate(self) -> float:
        """Percentage of eligible impressions that won auctions."""
        return safe_div(self.auctions_won, self.eligible_impressions)

    @computed_field
    @property
    def error_rate(self) -> float:
        """Error rate as percentage of requests."""
        return safe_div(self.error_count, self.requests)

    @computed_field
    @property
    def timeout_rate(self) -> float:
        """Timeout rate as percentage of requests."""
        return safe_div(self.timeout_count, self.requests)

    @computed_field
    @property
    def ctr_recalc(self) -> float:
        """Recalculated CTR (clicks/impressions)."""
        return safe_div(self.clicks, self.impressions)

    @computed_field
    @property
    def ctr(self) -> float:
        """CTR: sum(clicks) / sum(impressions)."""
        return safe_div(self.clicks, self.impressions)

    @computed_field
    @property
    def completion_rate(self) -> float:
        """Completion rate: sum(video_q100) / NULLIF(sum(video_start), 0) (0-1 ratio)."""
        if self.video_start == 0:
            return 0.0
        return self.video_q100 / self.video_start

    @computed_field
    @property
    def render_rate(self) -> float:
        """Render rate: sum(viewable_impressions) / sum(impressions) (proxy)."""
        return safe_div(self.viewable_impressions, self.impressions)

    @computed_field
    @property
    def fill_rate(self) -> float:
        """Fill rate: sum(auctions_won) / NULLIF(sum(eligible_impressions), 0)."""
        if self.eligible_impressions == 0:
            return 0.0
        return self.auctions_won / self.eligible_impressions

    @computed_field
    @property
    def response_rate(self) -> float:
        """Response rate: sum(responses) / NULLIF(sum(requests), 0)."""
        if self.requests == 0:
            return 0.0
        return self.responses / self.requests

    @computed_field
    @property
    def video_skip_rate(self) -> float:
        """Video skip rate: sum(skips) / NULLIF(sum(video_start), 0)."""
        if self.video_start == 0:
            return 0.0
        return self.skips / self.video_start


def add_extended_metrics_to_performance(campaign_id: int) -> int:
    """
    Compute derived metrics for existing raw rows and populate the extended performance table.
    Returns the number of rows processed and inserted into the extended table.
    """
    with session_scope() as s:
        # Get raw performance data from the basic table
        raw_rows = (
            s.execute(
                select(registry.CampaignPerformance).where(registry.CampaignPerformance.campaign_id == campaign_id)
            )
            .scalars()
            .all()
        )

        if not raw_rows:
            return 0

        # Clear existing extended performance data for this campaign
        s.query(registry.CampaignPerformanceExtended).filter(
            registry.CampaignPerformanceExtended.campaign_id == campaign_id
        ).delete()

        processed = 0
        for raw_row in raw_rows:
            # Create the Pydantic model to compute calculated fields
            extended_metrics = ExtendedPerformanceMetrics.model_validate(
                {
                    "campaign_id": raw_row.campaign_id,
                    "hour_ts": raw_row.hour_ts,
                    "impressions": raw_row.impressions,
                    "clicks": raw_row.clicks,
                    "video_start": raw_row.video_start,
                    "frequency": raw_row.frequency,
                    "reach": raw_row.reach,
                    "audience_json": raw_row.audience_json,
                    "requests": raw_row.requests,
                    "responses": raw_row.responses,
                    "eligible_impressions": raw_row.eligible_impressions,
                    "auctions_won": raw_row.auctions_won,
                    "viewable_impressions": raw_row.viewable_impressions,
                    "audible_impressions": raw_row.audible_impressions,
                    "video_q25": raw_row.video_q25,
                    "video_q50": raw_row.video_q50,
                    "video_q75": raw_row.video_q75,
                    "video_q100": raw_row.video_q100,
                    "skips": raw_row.skips,
                    "qr_scans": raw_row.qr_scans,
                    "interactive_engagements": raw_row.interactive_engagements,
                    "spend": raw_row.spend,
                    "error_count": raw_row.error_count,
                    "timeout_count": raw_row.timeout_count,
                    "hour_of_day": raw_row.hour_of_day,
                    "minute_of_hour": raw_row.minute_of_hour,
                    "second_of_minute": raw_row.second_of_minute,
                    "day_of_week": raw_row.day_of_week,
                    "is_business_hour": raw_row.is_business_hour,
                    "daily_day_date": raw_row.daily_day_date,
                    "weekly_start_day_date": raw_row.weekly_start_day_date,
                    "monthly_start_day_date": raw_row.monthly_start_day_date,
                    "human_readable": raw_row.human_readable,
                }
            )

            # Calculate avg_watch_time_seconds (estimated from quartiles)
            asset_seconds = 30.0
            if raw_row.video_start > 0:
                seg0 = max(0, raw_row.video_start - raw_row.video_q25)  # 0-25%
                seg1 = max(0, raw_row.video_q25 - raw_row.video_q50)  # 25-50%
                seg2 = max(0, raw_row.video_q50 - raw_row.video_q75)  # 50-75%
                seg3 = max(0, raw_row.video_q75 - raw_row.video_q100)  # 75-100%
                seg4 = max(0, raw_row.video_q100)  # 100%

                m0, m1, m2, m3, m4 = (0.125, 0.375, 0.625, 0.875, 1.0)
                total_watch = (
                    seg0 * (asset_seconds * m0)
                    + seg1 * (asset_seconds * m1)
                    + seg2 * (asset_seconds * m2)
                    + seg3 * (asset_seconds * m3)
                    + seg4 * (asset_seconds * m4)
                )
                avg_watch_time = int(total_watch / float(raw_row.video_start))
            else:
                avg_watch_time = 0

            # Create extended performance row
            extended_row = registry.CampaignPerformanceExtended(
                campaign_id=raw_row.campaign_id,
                hour_ts=raw_row.hour_ts,
                hour_unix_epoch=raw_row.hour_unix_epoch,
                requests=raw_row.requests,
                responses=raw_row.responses,
                eligible_impressions=raw_row.eligible_impressions,
                auctions_won=raw_row.auctions_won,
                impressions=raw_row.impressions,
                viewable_impressions=raw_row.viewable_impressions,
                audible_impressions=raw_row.audible_impressions,
                video_starts=raw_row.video_start,
                video_q25=raw_row.video_q25,
                video_q50=raw_row.video_q50,
                video_q75=raw_row.video_q75,
                video_q100=raw_row.video_q100,
                skips=raw_row.skips,
                avg_watch_time_seconds=avg_watch_time,
                clicks=raw_row.clicks,
                qr_scans=raw_row.qr_scans,
                interactive_engagements=raw_row.interactive_engagements,
                reach=raw_row.reach,
                frequency=raw_row.frequency,
                spend=raw_row.spend,
                effective_cpm=int(extended_metrics.effective_cpm),
                error_count=raw_row.error_count,
                timeout_count=raw_row.timeout_count,
                comment="Generated extended metrics",
                human_readable=raw_row.human_readable,
                hour_of_day=raw_row.hour_of_day,
                minute_of_hour=raw_row.minute_of_hour,
                second_of_minute=raw_row.second_of_minute,
                day_of_week=raw_row.day_of_week,
                is_business_hour=raw_row.is_business_hour,
                daily_day_date=raw_row.daily_day_date,
                weekly_start_day_date=raw_row.weekly_start_day_date,
                monthly_start_day_date=raw_row.monthly_start_day_date,
                # Calculated fields - now using the new computed properties
                ctr_recalc=extended_metrics.ctr_recalc,
                ctr=extended_metrics.ctr,
                completion_rate=extended_metrics.completion_rate,
                render_rate=extended_metrics.render_rate,
                fill_rate=extended_metrics.fill_rate,
                response_rate=extended_metrics.response_rate,
                video_skip_rate=extended_metrics.video_skip_rate,
                viewability_rate=extended_metrics.viewability_rate,
                audibility_rate=extended_metrics.audibility_rate,
                video_start_rate=extended_metrics.video_start_rate,
                video_completion_rate=extended_metrics.video_completion_rate,
                video_skip_rate_ext=extended_metrics.video_skip_rate_ext,
                qr_scan_rate=extended_metrics.qr_scan_rate,
                interactive_rate=extended_metrics.interactive_rate,
                auction_win_rate=extended_metrics.auction_win_rate,
                error_rate=extended_metrics.error_rate,
                timeout_rate=extended_metrics.timeout_rate,
                supply_funnel_efficiency=extended_metrics.supply_funnel_efficiency,
            )

            s.add(extended_row)
            processed += 1

        s.commit()
        return processed


# Back-compat shim
def generate_hourly_performance_ext(campaign_id: int, seed: Optional[int] = None, replace: bool = True) -> int:
    """
    Legacy function that now just adds calculated fields to existing performance data.

    This function no longer generates data - it only adds calculated metrics
    to existing performance rows.

    Args:
        campaign_id: Campaign identifier
        seed: Ignored (no data generation)
        replace: Ignored (no data generation)

    Returns:
        Number of rows processed
    """
    return add_extended_metrics_to_performance(campaign_id)


# ===== NETFLIX CORE ADVERTISING METRICS MAPPING =====
#
# This module now focuses on computing derived metrics from existing performance data.
# The core metrics follow Netflix's definitions and are computed using Pydantic models:
#
# 1. Impressions: Total ad impressions served (from existing data)
# 2. Clicks: Total click-through interactions (from existing data)
# 3. CTR: Click-through rate (clicks/impressions) - COMPUTED FROM EXISTING DATA
# 4. Video Completion Rate: Via q100 quartile (10%-70% completion) - COMPUTED FROM EXISTING DATA
# 5. Render Rate: Via viewability (95%-99% typical for Netflix) - COMPUTED FROM EXISTING DATA
# 6. Fill Rate: Via supply funnel (85%-98% typical) - COMPUTED FROM EXISTING DATA
# 7. Response Rate: Interactive engagement (1%-5% typical) - COMPUTED FROM EXISTING DATA
# 8. Video Skip Rate: Video skips (10%-40% typical) - COMPUTED FROM EXISTING DATA
# 9. Video Start: Video begins (70%-99% of impressions) - COMPUTED FROM EXISTING DATA
#
# All metrics are computed from existing performance data, eliminating duplication.
