from datetime import datetime, timedelta
from typing import Any, Dict


def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default value if denominator is zero.

    Args:
        numerator: The number to divide
        denominator: The number to divide by
        default: Value to return if denominator is zero (default: 0.0)

    Returns:
        numerator / denominator, or default if denominator is zero
    """
    if denominator == 0:
        return default
    return numerator / denominator


def generate_temporal_fields(hour: datetime) -> Dict[str, Any]:
    """
    Generate temporal breakdown fields for performance data.

    Args:
        hour: The hour timestamp to extract fields from

    Returns:
        Dictionary containing all temporal fields
    """
    from datetime import date

    # Calculate date fields
    daily_day_date = hour.date()

    # Calculate weekly start date (Monday)
    days_since_monday = hour.weekday()  # Monday=0, Sunday=6
    weekly_start_day_date = daily_day_date - timedelta(days=days_since_monday)

    # Calculate monthly start date (first day of month)
    monthly_start_day_date = date(hour.year, hour.month, 1)

    return {
        "hour_unix_epoch": int(hour.timestamp()),
        "human_readable": hour.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "hour_of_day": hour.hour,
        "minute_of_hour": hour.minute,
        "second_of_minute": hour.second,
        "day_of_week": hour.weekday(),  # Monday=0, Sunday=6
        "is_business_hour": 1 if 9 <= hour.hour <= 17 and hour.weekday() < 5 else 0,
        "daily_day_date": daily_day_date,
        "weekly_start_day_date": weekly_start_day_date,
        "monthly_start_day_date": monthly_start_day_date,
    }


def create_performance_row(
    model_class, campaign_id: int, hour: datetime, base_fields: Dict[str, Any], **additional_fields
):
    """
    Create a performance row with common fields and temporal breakdown.

    Args:
        model_class: The ORM model class to instantiate
        campaign_id: Campaign identifier
        hour: Hour timestamp
        base_fields: Base performance metrics
        **additional_fields: Additional fields specific to the model

    Returns:
        ORM model instance
    """
    temporal_fields = generate_temporal_fields(hour)

    return model_class(campaign_id=campaign_id, hour_ts=hour, **base_fields, **temporal_fields, **additional_fields)


def get_campaign_and_flight(session, campaign_id: int):
    """
    Get campaign and flight data for performance generation.

    Args:
        session: Database session
        campaign_id: Campaign identifier

    Returns:
        Tuple of (campaign, flight) or (None, None) if not found
    """
    from sqlalchemy import select

    from models.registry import registry

    camp = session.execute(select(registry.Campaign).where(registry.Campaign.id == campaign_id)).scalar_one_or_none()

    if camp is None:
        return None, None

    flight = session.execute(
        select(registry.Flight).where(registry.Flight.campaign_id == campaign_id)
    ).scalar_one_or_none()

    if flight is None:
        return None, None

    return camp, flight


def clear_existing_performance(session, model_class, campaign_id: int):
    """
    Clear existing performance data for a campaign.

    Args:
        session: Database session
        model_class: The ORM model class to clear
        campaign_id: Campaign identifier
    """
    from sqlalchemy import delete

    session.execute(delete(model_class).where(model_class.campaign_id == campaign_id))


def batch_insert_performance(session, rows: list):
    """
    Batch insert performance rows.

    Args:
        session: Database session
        rows: List of ORM model instances to insert
    """
    session.bulk_save_objects(rows)
    session.flush()
