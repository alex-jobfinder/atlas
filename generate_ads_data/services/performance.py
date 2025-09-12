"""
Basic performance generation utilities - RAW DATA ONLY.

This module generates only raw performance metrics without any calculated fields.
All derived metrics (rates, percentages) are computed elsewhere using Pydantic models.

Modeled effects (inspired by jafgen):
- Hour-of-day: Gaussian uplift during 09:00–17:00, peaking at 13:00.
- Day-of-week: Weekends less busy than weekdays (Fri 0.97, Sat 0.88, Sun 0.92).
- Flight ramp: Logistic S-curve (~0.85→1.15) with mild weekly undulation.
- Annual seasonality: Cosine by day-of-year (~0.8→1.0) for gentle yearly swings.

Public API
- generate_hourly_performance_raw(campaign_id, seed=None, replace=True) -> int
  Creates one row per hour (UTC boundary) across the campaign flight in
  `CampaignPerformance` with ONLY raw data. No calculated fields are generated.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from random import Random
from typing import Iterable

from db_utils import session_scope
from models.registry import registry
from services.performance_utils import (
    batch_insert_performance,
    clear_existing_performance,
    create_performance_row,
    get_campaign_and_flight,
)


class TimestampDataGenerator:
    """Generate temporal factors for performance data generation."""

    def __init__(self):
        pass

    def hourly_boost(self, dt: datetime) -> float:
        """Return a multiplicative uplift factor for the given hour.

        Uses a Gaussian centered at 13:00 with sigma=2.5 between 9:00 and 17:00,
        yielding a maximum uplift of ~1.5 at the peak and tapering near edges.
        Outside that window, returns 1.0 (no boost).
        """
        hour = dt.hour
        if 9 <= hour <= 17:
            mu = 13.0
            sigma = 2.5
            x = (hour - mu) / sigma
            g = math.exp(-0.5 * x * x)
            return 1.0 + 0.45 * g
        return 1.0

    def dow_factor(self, dt: datetime) -> float:
        """Day-of-week multiplier: weekends slightly less busy than weekdays.

        Mon..Thu ~ 1.00, Fri 0.97, Sat 0.88, Sun 0.92
        """
        wd = dt.weekday()  # Mon=0 .. Sun=6
        if wd == 4:  # Fri
            return 0.97
        if wd == 5:  # Sat
            return 0.88
        if wd == 6:  # Sun
            return 0.92
        return 1.00

    def ramp_factor(self, start_dt: datetime, current_dt: datetime, end_dt: datetime) -> float:
        """Smooth ramp over the flight to emulate 'store openings' or audience growth.

        Uses a logistic-like S-curve scaled to ~[0.85, 1.15] across the flight,
        with slight weekly undulation to mimic weekly cycles.
        """
        total_hours = max(1.0, (end_dt - start_dt).total_seconds() / 3600.0)
        t = min(1.0, max(0.0, (current_dt - start_dt).total_seconds() / 3600.0 / total_hours))
        # Logistic-ish curve centered at mid-flight
        x = (t - 0.5) * 6.0
        s = 1.0 / (1.0 + math.exp(-x))  # 0..1
        ramp = 0.85 + 0.30 * s  # 0.85..1.15
        # Mild weekly undulation (period ~168 hours)
        weekly = 1.0 + 0.03 * math.sin(2.0 * math.pi * (current_dt - start_dt).total_seconds() / (168.0 * 3600.0))
        return ramp * weekly

    def annual_factor(self, dt: datetime) -> float:
        """Annual seasonality factor similar to jafgen's AnnualCurve.

        Cosine over day-of-year scaled to roughly [0.8, 1.0].
        """
        # Day of year in [1..366]; use 365 as baseline period
        yday = dt.timetuple().tm_yday
        x = 2.0 * math.pi * (yday - 1) / 365.0
        return (math.cos(x) + 1.0) / 10.0 + 0.8

    def calculate_temporal_factor(self, start_dt: datetime, current_dt: datetime, end_dt: datetime) -> float:
        """Calculate combined temporal factor from all components."""
        hod_factor = self.hourly_boost(current_dt)
        dow_factor = self.dow_factor(current_dt)
        ramp_factor = self.ramp_factor(start_dt, current_dt, end_dt)
        annual_factor = self.annual_factor(current_dt)

        return hod_factor * dow_factor * ramp_factor * annual_factor


def _hours_between(start_dt: datetime, end_dt: datetime) -> Iterable[datetime]:
    """Yield hourly timestamps inclusive between start_dt and end_dt.

    - Timestamps are assumed to be timezone-aware and aligned by caller.
    - End is inclusive because hourly reporting typically includes the
      terminal hour for same-day flights.
    """
    current = start_dt
    while current <= end_dt:
        yield current
        current = current + timedelta(hours=1)

def generate_hourly_performance_raw(campaign_id: int, seed: int | None = None, replace: bool = True) -> int:
    """Generate hourly performance for a campaign across its flight window (RAW first, then calculated)."""
    rng = Random(seed)
    ts = TimestampDataGenerator()

    with session_scope() as s:
        camp, flight = get_campaign_and_flight(s, campaign_id)
        if camp is None or flight is None:
            return 0

        start_dt = datetime.combine(flight.start_date, datetime.min.time(), tzinfo=timezone.utc)
        end_dt = datetime.combine(flight.end_date, datetime.max.time(), tzinfo=timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )

        if replace:
            clear_existing_performance(s, registry.CampaignPerformance, campaign_id)

        rows = 0
        all_rows = []

        for hour in _hours_between(start_dt, end_dt):
            factor = ts.calculate_temporal_factor(start_dt, hour, end_dt)

            # -----------------------------
            # 1) PURE SUMS / COUNTS (RAW)
            # -----------------------------
            base_impressions = rng.randint(1000, 10000)
            impressions = int(max(1, base_impressions * factor))

            # clicks driven by a latent click-propensity (rate) but stored as a count
            base_ctr = rng.uniform(0.001, 0.02)            # latent
            ctr_variance = rng.uniform(0.8, 1.2)           # latent
            raw_ctr = min(0.05, max(0.0001, base_ctr * ctr_variance * factor))  # latent
            clicks = max(0, int(impressions * raw_ctr))

            # video starts (count)
            base_start_rate = rng.uniform(0.80, 0.95)      # latent
            start_factor = min(0.99, max(0.70, base_start_rate * factor))       # latent
            video_start = max(0, int(impressions * start_factor))

            # quartiles (counts; enforce q25 >= q50 >= q75 >= q100)
            q25 = int(video_start * max(0.60, min(0.98, rng.uniform(0.70, 0.95))))
            q50 = int(video_start * max(0.40, min(0.90, rng.uniform(0.55, 0.90))))
            q75 = int(video_start * max(0.25, min(0.80, rng.uniform(0.40, 0.80))))
            q100 = int(video_start * max(0.10, min(0.70, rng.uniform(0.25, 0.70))))
            q50 = min(q50, q25); q75 = min(q75, q50); q100 = min(q100, q75)

            # requests/responses (counts)
            requests = int(impressions * rng.uniform(1.1, 1.8))
            min_responses = int(0.9 * requests) + 1
            responses = max(min_responses, int(impressions * rng.uniform(0.92, 1.04)))

            # eligible / auctions won (counts)
            min_eligible = int(0.8 * responses) + 1
            eligible_impressions = max(min_eligible, int(impressions * rng.uniform(0.90, 0.99)))
            min_auctions = int(0.8 * eligible_impressions) + 1
            auctions_won_candidate = int(impressions * rng.uniform(0.90, 0.99))
            auctions_won = min(eligible_impressions, max(min_auctions, auctions_won_candidate))

            # viewable / audible impressions (counts)
            # Ensure high viewability in realistic range (90%–99%)
            viewable_impressions = int(impressions * rng.uniform(0.90, 0.99))
            audible_impressions = int(
                impressions
                * max(0.20, min(0.95, rng.uniform(0.35, 0.80) * (1.05 if hour.hour >= 18 or hour.hour <= 22 else 0.95)))
            )

            # engagement-esque counts
            skips = int(video_start * max(0.05, min(0.60, rng.uniform(0.10, 0.40) * (2.0 - min(1.5, factor)))))
            qr_scans = int(impressions * rng.uniform(0.0003, 0.006))
            interactive_engagements = int(impressions * rng.uniform(0.001, 0.02))

            # money / reliability counts
            spend = int(
                (impressions * rng.randint(1200, 4500) * rng.uniform(0.9, 1.1) * (0.95 + 0.1 * min(1.5, factor))) // 1000
            )
            error_count = int(impressions * rng.uniform(0.0005, 0.004))
            timeout_count = int(impressions * rng.uniform(0.0005, 0.003))

            # frequency / reach (counts)
            base_frequency = rng.randint(1, 4)
            frequency = max(1, min(5, int(round(base_frequency * (1.0 + 0.15 * max(0.0, factor - 1.0))))))
            reach = max(1, impressions // max(1, frequency))

            # -----------------------------
            # 2) CALCULATED / RATIO FIELDS - REMOVED
            #    These metrics are now computed in performance_ext.py using the formulas:
            #    - ctr: sum(clicks) / sum(impressions)
            #    - completion_rate: sum(video_q100) / NULLIF(sum(video_start), 0) × 100
            #    - render_rate: sum(viewable_impressions) / sum(impressions) (proxy)
            #    - fill_rate: sum(auctions_won) / NULLIF(sum(eligible_impressions), 0)
            #    - response_rate: sum(responses) / NULLIF(sum(requests), 0)
            #    - video_skip_rate: sum(skips) / NULLIF(sum(video_start), 0)
            # -----------------------------

            # audience mix (json)
            audience_json = json.dumps(_audience_mix(rng, hour, impressions))

            base_fields = {
                # ---- SUMS / COUNTS ----
                "impressions": impressions,
                "clicks": clicks,
                "video_start": video_start,
                "video_q25": q25,
                "video_q50": q50,
                "video_q75": q75,
                "video_q100": q100,
                "requests": requests,
                "responses": responses,
                "eligible_impressions": eligible_impressions,
                "auctions_won": auctions_won,
                "viewable_impressions": viewable_impressions,
                "audible_impressions": audible_impressions,
                "skips": skips,
                "qr_scans": qr_scans,
                "interactive_engagements": interactive_engagements,
                "spend": spend,
                "error_count": error_count,
                "timeout_count": timeout_count,
                "frequency": frequency,
                "reach": reach,

                # ---- METADATA ----
                "audience_json": audience_json,
            }

            perf = create_performance_row(registry.CampaignPerformance, campaign_id, hour, base_fields)
            all_rows.append(perf)
            rows += 1

        batch_insert_performance(s, all_rows)
        return rows



def _audience_mix(rng: Random, dt: datetime, impressions: int) -> dict:
    """Generate a simple audience composition snapshot aligned with preferences.

    Returns percentages (0..1) across segments. Sums may be ~1.0 after rounding.
    """
    # Device preferences: more CTV evenings/weekends, more MOBILE weekdays daytime
    is_weekend = dt.weekday() in (5, 6)
    evening = dt.hour >= 18 or dt.hour <= 22
    base_device = {
        "CTV": 0.45 if (is_weekend or evening) else 0.30,
        "DESKTOP": 0.20 if (is_weekend or evening) else 0.30,
        "MOBILE": 0.35 if (is_weekend or evening) else 0.40,
    }
    # Age buckets skew slightly older weekday daytime, younger evenings/weekends
    base_age = {
        "18-24": 0.16 if (is_weekend or evening) else 0.12,
        "25-34": 0.24,
        "35-44": 0.22,
        "45-54": 0.18,
        "55-64": 0.13,
        "65+": 0.07,
    }

    # Normalize helper
    def _normalize(d: dict[str, float]) -> dict[str, float]:
        s = sum(d.values()) or 1.0
        return {k: v / s for k, v in d.items()}

    device = _normalize(base_device)
    age = _normalize(base_age)
    gender = {"F": 0.5, "M": 0.5}
    life_stage = {"SINGLE": 0.35, "PARENT": 0.40, "EMPTY_NEST": 0.25}
    interest = {"SPORTS": 0.20, "ENTERTAINMENT": 0.30, "FOOD": 0.20, "TECH": 0.15, "TRAVEL": 0.15}

    return {
        "device": device,
        "age": age,
        "gender": gender,
        "life_stage": life_stage,
        "interest": interest,
    }


# Legacy function name for backward compatibility
def generate_hourly_performance(campaign_id: int, seed: int | None = None, replace: bool = True) -> int:
    """Legacy function that calls the new raw data generator."""
    return generate_hourly_performance_raw(campaign_id, seed, replace)
