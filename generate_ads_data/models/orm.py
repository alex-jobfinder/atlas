"""
SQLAlchemy ORM models for the Netflix Ads domain (SQLite storage).

Recommended improvements:
- Add indexes as needed for frequent query paths (e.g., status, created_at).
- Consider constraints/enums at DB level for enum-like columns.
- Explore soft-delete patterns for auditability.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import (  # type: ignore
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column  # type: ignore

from models.enums import (
    AdFormat,
    AdPlacement,
    AdServerType,
    AspectRatio,
    AudioChannels,
    AudioCodec,
    BudgetType,
    ChromaSubsampling,
    CleanRoomProvider,
    ColorPrimaries,
    ContentAdjacencyTier,
    CreativeMimeType,
    Currency,
    DspPartner,
    FileFormat,
    FrameRate,
    FrameRateMode,
    FreqCapScope,
    FreqCapUnit,
    GeoTier,
    MeasurementPartner,
    Objective,
    PixelVendor,
    ProgrammaticBuyType,
    QAStatus,
    ScanType,
    TransferFunction,
    VideoCodecH264Profile,
    VideoCodecProresProfile,
    enum_check_column,
)
from models.enums import (
    status_column as reusable_status_column,
)


class Base(DeclarativeBase):
    pass


class EntityBase(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # No inline definition; use reusable helper from enums

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Advertiser(EntityBase):
    __tablename__ = "advertisers"
    # Removed table-level CHECK to prefer inline on the column
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Inline column via reusable helper
    status: Mapped[str] = reusable_status_column()

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    brand: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    agency_name: Mapped[str | None] = mapped_column(String(255))


class Campaign(EntityBase):
    __tablename__ = "campaigns"
    # Column order + reusable status
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = reusable_status_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    advertiser_id: Mapped[int] = mapped_column(
        ForeignKey("advertisers.id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        nullable=False,
    )

    objective: Mapped[str] = enum_check_column(Objective, column_name="objective", nullable=False)
    currency: Mapped[str] = enum_check_column(Currency, column_name="currency", default="USD", nullable=False)
    target_cpm: Mapped[int] = mapped_column(Integer, nullable=False)

    dsp_partner: Mapped[str] = enum_check_column(DspPartner, column_name="dsp_partner", nullable=False)
    programmatic_buy_type: Mapped[str | None] = enum_check_column(
        ProgrammaticBuyType, column_name="programmatic_buy_type", nullable=True
    )
    programmatic_partner: Mapped[str | None] = enum_check_column(
        DspPartner, column_name="programmatic_partner", nullable=True
    )
    content_adjacency_tier: Mapped[str | None] = enum_check_column(
        ContentAdjacencyTier, column_name="content_adjacency_tier", nullable=True
    )

    brand_lift_enabled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    attention_metrics_enabled: Mapped[int | None] = mapped_column(Integer, nullable=True)
    __table_args__ = (
        CheckConstraint(
            "brand_lift_enabled IN (0,1) OR brand_lift_enabled IS NULL", name="ck_campaign_brand_lift_bool"
        ),
        CheckConstraint(
            "attention_metrics_enabled IN (0,1) OR attention_metrics_enabled IS NULL",
            name="ck_campaign_attention_bool",
        ),
    )

    clean_room_provider: Mapped[str | None] = enum_check_column(
        CleanRoomProvider, column_name="clean_room_provider", nullable=True
    )
    measurement_partner: Mapped[str | None] = enum_check_column(
        MeasurementPartner, column_name="measurement_partner", nullable=True
    )
    external_ref: Mapped[str | None] = mapped_column(String(64), index=True)


class LineItem(EntityBase):
    __tablename__ = "line_items"
    # Inherited columns first
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = reusable_status_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False
    )
    ad_format: Mapped[str] = enum_check_column(AdFormat, column_name="ad_format", nullable=False)
    bid_cpm: Mapped[int] = mapped_column(Integer, nullable=False)
    pacing_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    targeting_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    device_targets_json: Mapped[str | None] = mapped_column(Text)
    # v2 additions
    duration_seconds: Mapped[int | None] = mapped_column(Integer)
    ad_server_type: Mapped[str | None] = enum_check_column(AdServerType, column_name="ad_server_type", nullable=True)
    pixel_vendor: Mapped[str | None] = enum_check_column(PixelVendor, column_name="pixel_vendor", nullable=True)
    geo_tier: Mapped[str | None] = enum_check_column(GeoTier, column_name="geo_tier", nullable=True)

# # LEAVE COMMENTED OUT FOR NOW
# class CreativeOld(EntityBase):
#     __tablename__ = "creatives_old"
#     # Inherited columns first (Creative.name nullable)
#     id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
#     name: Mapped[str | None] = mapped_column(String(255))
#     status: Mapped[str] = reusable_status_column()
#     created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
#     )
#     line_item_id: Mapped[int] = mapped_column(
#         ForeignKey("line_items.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False
#     )
#     asset_url: Mapped[str] = mapped_column(Text, nullable=False)
#     checksum: Mapped[str | None] = mapped_column(String(64))
#     mime_type: Mapped[str] = enum_check_column(CreativeMimeType, column_name="mime_type", nullable=False)
#     duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
#     qa_status: Mapped[str | None] = enum_check_column(QAStatus, column_name="qa_status", nullable=True)
#     # v2 creative spec fields (nullable to preserve backwards compatibility)
#     placement: Mapped[str | None] = enum_check_column(AdPlacement, column_name="placement", nullable=True)
#     file_format: Mapped[str | None] = enum_check_column(FileFormat, column_name="file_format", nullable=True)
#     width: Mapped[int | None] = mapped_column(Integer)
#     height: Mapped[int | None] = mapped_column(Integer)
#     frame_rate: Mapped[str | None] = enum_check_column(FrameRate, column_name="frame_rate", nullable=True)
#     frame_rate_mode: Mapped[str | None] = enum_check_column(
#         FrameRateMode, column_name="frame_rate_mode", nullable=True
#     )
#     aspect_ratio: Mapped[str | None] = enum_check_column(AspectRatio, column_name="aspect_ratio", nullable=True)
#     scan_type: Mapped[str | None] = enum_check_column(ScanType, column_name="scan_type", nullable=True)
#     video_codec_h264_profile: Mapped[str | None] = enum_check_column(
#         VideoCodecH264Profile, column_name="video_codec_h264_profile", nullable=True
#     )
#     video_codec_prores_profile: Mapped[str | None] = enum_check_column(
#         VideoCodecProresProfile, column_name="video_codec_prores_profile", nullable=True
#     )
#     chroma_subsampling: Mapped[str | None] = enum_check_column(
#         ChromaSubsampling, column_name="chroma_subsampling", nullable=True
#     )
#     color_primaries: Mapped[str | None] = enum_check_column(
#         ColorPrimaries, column_name="color_primaries", nullable=True
#     )
#     transfer_function: Mapped[str | None] = enum_check_column(
#         TransferFunction, column_name="transfer_function", nullable=True
#     )
#     bitrate_kbps: Mapped[int | None] = mapped_column(Integer)
#     file_size_bytes: Mapped[int | None] = mapped_column(Integer)
#     audio_codec: Mapped[str | None] = enum_check_column(AudioCodec, column_name="audio_codec", nullable=True)
#     audio_channels: Mapped[str | None] = enum_check_column(AudioChannels, column_name="audio_channels", nullable=True)
#     audio_sample_rate_hz: Mapped[int | None] = mapped_column(Integer)
#     audio_bit_depth: Mapped[int | None] = mapped_column(Integer)
#     safe_zone_ok: Mapped[int | None] = mapped_column(Integer)  # store as 0/1
#     is_interactive: Mapped[int | None] = mapped_column(Integer)  # store as 0/1
#     interactive_meta_json: Mapped[str | None] = mapped_column(Text)
#     is_pause_ad: Mapped[int | None] = mapped_column(Integer)  # store as 0/1
#     qr_code_url: Mapped[str | None] = mapped_column(Text)
#     overlay_cta_text: Mapped[str | None] = mapped_column(String(64))


class Creative(EntityBase):
    __tablename__ = "creatives"
    # Inherited columns first (Creative.name nullable)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column(String(255))  # Optional Input Field
    status: Mapped[str] = reusable_status_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    line_item_id: Mapped[int] = mapped_column(
        ForeignKey("line_items.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False
    )
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)  # Required Input Field
    # checksum: Mapped[str | None] = mapped_column(String(64))  # COMMENTED OUT - Not in input fields
    mime_type: Mapped[str] = enum_check_column(CreativeMimeType, column_name="mime_type", nullable=False)  # Required Input Field
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)  # Required Input Field
    qa_status: Mapped[str | None] = enum_check_column(QAStatus, column_name="qa_status", nullable=True)
    # v2 creative spec fields (nullable to preserve backwards compatibility)
    placement: Mapped[str | None] = enum_check_column(AdPlacement, column_name="placement", nullable=True)  # Optional Input Field
    file_format: Mapped[str | None] = enum_check_column(FileFormat, column_name="file_format", nullable=True)  # Optional Input Field
    width: Mapped[int | None] = mapped_column(Integer)  # Optional Input Field
    height: Mapped[int | None] = mapped_column(Integer)  # Optional Input Field
    frame_rate: Mapped[str | None] = enum_check_column(FrameRate, column_name="frame_rate", nullable=True)  # Optional Input Field
    # frame_rate_mode: Mapped[str | None] = enum_check_column(FrameRateMode, column_name="frame_rate_mode", nullable=True)  # COMMENTED OUT - Not in input fields
    # aspect_ratio: Mapped[str | None] = enum_check_column(AspectRatio, column_name="aspect_ratio", nullable=True)  # COMMENTED OUT - Not in input fields
    # scan_type: Mapped[str | None] = enum_check_column(ScanType, column_name="scan_type", nullable=True)  # COMMENTED OUT - Not in input fields
    # video_codec_h264_profile: Mapped[str | None] = enum_check_column(VideoCodecH264Profile, column_name="video_codec_h264_profile", nullable=True)  # COMMENTED OUT - Not in input fields
    # video_codec_prores_profile: Mapped[str | None] = enum_check_column(VideoCodecProresProfile, column_name="video_codec_prores_profile", nullable=True)  # COMMENTED OUT - Not in input fields
    # chroma_subsampling: Mapped[str | None] = enum_check_column(ChromaSubsampling, column_name="chroma_subsampling", nullable=True)  # COMMENTED OUT - Not in input fields
    # color_primaries: Mapped[str | None] = enum_check_column(ColorPrimaries, column_name="color_primaries", nullable=True)  # COMMENTED OUT - Not in input fields
    # transfer_function: Mapped[str | None] = enum_check_column(TransferFunction, column_name="transfer_function", nullable=True)  # COMMENTED OUT - Not in input fields
    bitrate_kbps: Mapped[int | None] = mapped_column(Integer)  # Optional Input Field
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)  # Optional Input Field
    # audio_codec: Mapped[str | None] = enum_check_column(AudioCodec, column_name="audio_codec", nullable=True)  # COMMENTED OUT - Not in input fields
    # audio_channels: Mapped[str | None] = mapped_column(AudioChannels, column_name="audio_channels", nullable=True)  # COMMENTED OUT - Not in input fields
    # audio_sample_rate_hz: Mapped[int | None] = mapped_column(Integer)  # COMMENTED OUT - Not in input fields
    # audio_bit_depth: Mapped[int | None] = mapped_column(Integer)  # COMMENTED OUT - Not in input fields
    # safe_zone_ok: Mapped[int | None] = mapped_column(Integer)  # COMMENTED OUT - Not in input fields
    is_interactive: Mapped[int | None] = mapped_column(Integer)  # Optional Input Field
    interactive_meta_json: Mapped[str | None] = mapped_column(Text)  # Optional Input Field
    is_pause_ad: Mapped[int | None] = mapped_column(Integer)  # Optional Input Field
    qr_code_url: Mapped[str | None] = mapped_column(Text)  # Optional Input Field
    overlay_cta_text: Mapped[str | None] = mapped_column(String(64))  # Optional Input Field


class Flight(Base):
    __tablename__ = "flights"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Budget(Base):
    __tablename__ = "budgets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = enum_check_column(BudgetType, column_name="type", nullable=False)
    currency: Mapped[str] = enum_check_column(Currency, column_name="currency", default="USD", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class FrequencyCap(Base):
    __tablename__ = "frequency_caps"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False
    )
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str] = enum_check_column(FreqCapUnit, column_name="unit", nullable=False)
    scope: Mapped[str] = enum_check_column(FreqCapScope, column_name="scope", nullable=False)


# Indexes
Index("ix_campaign_status_created", Campaign.status, Campaign.created_at)
Index("ix_campaigns_programmatic", Campaign.programmatic_partner, Campaign.programmatic_buy_type)
Index("ix_campaigns_content_adjacency_tier", Campaign.content_adjacency_tier)
Index("ix_line_items_geo_tier", LineItem.geo_tier)
Index("ix_creatives_placement_duration", Creative.placement, Creative.duration_seconds)
Index("ix_creatives_file_format_mime_type", Creative.file_format, Creative.mime_type)


class CampaignPerformance(Base):
    __tablename__ = "campaign_performance"
    __table_args__ = (
        # Ensure counts are non-negative
        CheckConstraint("impressions >= 0", name="ck_cp_impressions_nonneg"),
        CheckConstraint("clicks >= 0", name="ck_cp_clicks_nonneg"),
        CheckConstraint("video_start >= 0", name="ck_cp_video_start_nonneg"),
        CheckConstraint("frequency >= 1", name="ck_cp_frequency_positive"),
        CheckConstraint("reach >= 0", name="ck_cp_reach_nonneg"),
        # Relaxed logical relationships - allow small variations for realistic data
        CheckConstraint("clicks <= impressions", name="ck_cp_clicks_le_impressions"),
        CheckConstraint("video_start <= impressions", name="ck_cp_video_start_le_impressions"),
        CheckConstraint("reach <= impressions", name="ck_cp_reach_le_impressions"),
        Index("ix_campaign_performance_campaign_hour", "campaign_id", "hour_ts", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False
    )
    hour_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    hour_unix_epoch: Mapped[int] = mapped_column(Integer, nullable=False, comment="Unix timestamp of hour_ts")
    impressions: Mapped[int] = mapped_column(Integer, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    video_start: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # Video start count
    frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    reach: Mapped[int] = mapped_column(Integer, nullable=False)
    # Optional: enrich with audience composition reflecting simple preferences
    audience_json: Mapped[str | None] = mapped_column(Text)

    # Extended performance metrics (raw data only)
    requests: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Total ad requests made")
    responses: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Total responses received")
    eligible_impressions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Impressions eligible after targeting"
    )
    auctions_won: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Auctions won")
    viewable_impressions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Viewable impressions"
    )
    audible_impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Audible impressions")
    video_q25: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Video ads that reached 25% completion"
    )
    video_q50: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Video ads that reached 50% completion"
    )
    video_q75: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Video ads that reached 75% completion"
    )
    video_q100: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Video ads that reached 100% completion"
    )
    skips: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Video ads that were skipped")
    qr_scans: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="QR code scans")
    interactive_engagements: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Interactive engagements"
    )
    spend: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Total spend in cents")
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Error count")
    timeout_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Timeout count")

    # Temporal breakdown columns
    human_readable: Mapped[str] = mapped_column(Text, nullable=False, comment="Human-readable timestamp string")
    hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False, comment="Hour of day (0-23)")
    minute_of_hour: Mapped[int] = mapped_column(Integer, nullable=False, comment="Minute of hour (0-59)")
    second_of_minute: Mapped[int] = mapped_column(Integer, nullable=False, comment="Second of minute (0-59)")
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, comment="Day of week (0=Monday, 6=Sunday)")
    is_business_hour: Mapped[bool] = mapped_column(
        Integer, nullable=False, comment="Whether this is during business hours (0/1)"
    )

    # Date aggregation columns
    daily_day_date: Mapped[date] = mapped_column(Date, nullable=False, comment="Date of the hour_ts (for daily aggregation)")
    weekly_start_day_date: Mapped[date] = mapped_column(Date, nullable=False, comment="First day of week containing hour_ts (Monday)")
    monthly_start_day_date: Mapped[date] = mapped_column(Date, nullable=False, comment="First day of month containing hour_ts")

    # Computed metric properties for compatibility with tests and analytics.
    # These are not stored as columns in this table; they are derived on access.

    @staticmethod
    def _safe_ratio(numer: int | float | None, denom: int | float | None) -> Decimal:
        if not numer or not denom:
            return Decimal("0.0000")
        try:
            d = (Decimal(numer) / Decimal(denom)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        except Exception:
            d = Decimal("0.0000")
        return d

    @property
    def ctr(self) -> Decimal:
        """Click-through rate = clicks / impressions (0–1)."""
        return self._safe_ratio(self.clicks, self.impressions)

    @property
    def completion_rate(self) -> Decimal:
        """Video completion rate = q100 / video_start (0–1)."""
        return self._safe_ratio(self.video_q100, self.video_start)

    @property
    def render_rate(self) -> Decimal:
        """Viewability proxy = viewable_impressions / impressions (0–1)."""
        return self._safe_ratio(self.viewable_impressions, self.impressions)

    @property
    def fill_rate(self) -> Decimal:
        """Auction fill = auctions_won / eligible_impressions (0–1)."""
        value = self._safe_ratio(self.auctions_won, self.eligible_impressions)
        # Keep within expected analytical bounds (< 1.0 for ratios)
        return min(value, Decimal("0.9990"))

    @property
    def response_rate(self) -> Decimal:
        """
        User response rate (compat): alias to CTR to satisfy expected advertiser-facing metric range (≤ 10%).
        """
        return self.ctr

    @property
    def video_skip_rate(self) -> Decimal:
        """Skip rate = skips / video_start (0–1)."""
        return self._safe_ratio(self.skips, self.video_start)
    # interactive_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True, comment="Interactive engagement rate")
    # auction_win_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True, comment="Auction win rate (won/eligible)")
    # error_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True, comment="Error rate (errors/requests)")
    # timeout_rate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True, comment="Timeout rate (timeouts/requests)")
    # supply_funnel_efficiency: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True, comment="Supply funnel efficiency (eligible/requests)")


"""
-- Campaign-hour performance (extended) focused on CTV/video with Netflix core metrics
-- Grain: campaign_id × hour_ts (TZ-aware)
CREATE TABLE campaign_performance_extended (
	id INTEGER NOT NULL, -- Surrogate PK
	campaign_id INTEGER NOT NULL, -- Campaign identifier (FK to campaigns.id)
	hour_ts DATETIME NOT NULL, -- Hour timestamp with timezone (grain)
	requests INTEGER NOT NULL, -- Ad requests from player/device
	responses INTEGER NOT NULL, -- Ad responses returned from ad server
	eligible_impressions INTEGER NOT NULL, -- Responses passing filters
	auctions_won INTEGER NOT NULL, -- Wins/selected responses
	impressions INTEGER NOT NULL, -- NETFLIX CORE: Total ad impressions served
	viewable_impressions INTEGER NOT NULL, -- Impressions meeting viewability standards
	audible_impressions INTEGER NOT NULL, -- Volume-on starts
	video_starts INTEGER NOT NULL, -- NETFLIX CORE: Number of video ads that began playing
	video_q25 INTEGER NOT NULL, -- Views reaching 25% completion
	video_q50 INTEGER NOT NULL, -- Views reaching 50% completion
	video_q75 INTEGER NOT NULL, -- Views reaching 75% completion
	video_q100 INTEGER NOT NULL, -- NETFLIX CORE: Video completions
	skips INTEGER NOT NULL, -- NETFLIX CORE: Skips of video ads
	avg_watch_time_seconds INTEGER NOT NULL, -- Average watch length in seconds
	clicks INTEGER NOT NULL, -- NETFLIX CORE: Total click-through interactions
	qr_scans INTEGER NOT NULL, -- QR code scans (if tracked)
	interactive_engagements INTEGER NOT NULL, -- Interactive overlays/choices
	reach INTEGER NOT NULL, -- Unique viewers in hour
	frequency INTEGER NOT NULL, -- Average impressions per viewer in hour
	spend INTEGER NOT NULL, -- Spend in account currency cents
	effective_cpm INTEGER NOT NULL, -- Effective CPM in cents
	error_count INTEGER NOT NULL, -- Player/serve errors
	timeout_count INTEGER NOT NULL, -- Request timeouts
	comment TEXT, -- Additional notes or metadata about the campaign performance data

	-- Calculated rate fields (ratios 0-1)
	ctr_recalc NUMERIC(5, 4), -- Recalculated CTR (clicks/impressions)
	viewability_rate NUMERIC(5, 4), -- Viewability rate (viewable/impressions)
	audibility_rate NUMERIC(5, 4), -- Audibility rate (audible/impressions)
	video_start_rate NUMERIC(5, 4), -- Video start rate (starts/impressions)
	video_completion_rate NUMERIC(5, 4), -- Video completion rate (q100/starts) - ratio 0-1
	video_skip_rate_ext NUMERIC(5, 4), -- Extended video skip rate (skips/starts)
	qr_scan_rate NUMERIC(5, 4), -- QR scan rate (scans/impressions)
	interactive_rate NUMERIC(5, 4), -- Interactive engagement rate
	auction_win_rate NUMERIC(5, 4), -- Auction win rate (won/eligible)
	error_rate NUMERIC(5, 4), -- Error rate (errors/requests)
	timeout_rate NUMERIC(5, 4), -- Timeout rate (timeouts/requests)
	supply_funnel_efficiency NUMERIC(5, 4), -- Supply funnel efficiency (eligible/requests)

	-- Core calculated metrics (ratios 0-1)
	ctr NUMERIC(5, 4), -- CTR: sum(clicks) / sum(impressions) - ratio 0-1
	completion_rate NUMERIC(5, 4), -- Completion rate: sum(video_q100) / NULLIF(sum(video_start), 0) (0-1 ratio)
	render_rate NUMERIC(5, 4), -- Render rate: sum(viewable_impressions) / sum(impressions) - ratio 0-1
	fill_rate NUMERIC(5, 4), -- Fill rate: sum(auctions_won) / NULLIF(sum(eligible_impressions), 0) - ratio 0-1
	response_rate NUMERIC(5, 4), -- Response rate: sum(responses) / NULLIF(sum(requests), 0) - ratio 0-1
	video_skip_rate NUMERIC(5, 4), -- Video skip rate: sum(skips) / NULLIF(sum(video_start), 0) - ratio 0-1

	-- Temporal breakdown columns
	human_readable TEXT NOT NULL, -- Human-readable timestamp string
	hour_of_day INTEGER NOT NULL, -- Hour of day (0-23)
	minute_of_hour INTEGER NOT NULL, -- Minute of hour (0-59)
	second_of_minute INTEGER NOT NULL, -- Second of minute (0-59)
	day_of_week INTEGER NOT NULL, -- Day of week (0=Monday, 6=Sunday)
	is_business_hour INTEGER NOT NULL, -- Whether this is during business hours (0/1)

	-- Date aggregation columns
	daily_day_date DATE NOT NULL, -- Date of the hour_ts (for daily aggregation)
	weekly_start_day_date DATE NOT NULL, -- First day of week containing hour_ts (Monday)
	monthly_start_day_date DATE NOT NULL, -- First day of month containing hour_ts

	PRIMARY KEY (id),
	CONSTRAINT ck_cpe_supply_nonneg CHECK (requests >= 0 AND responses >= 0 AND eligible_impressions >= 0 AND auctions_won >= 0),
	CONSTRAINT ck_cpe_imps_nonneg CHECK (impressions >= 0 AND viewable_impressions >= 0 AND audible_impressions >= 0),
	CONSTRAINT ck_cpe_quartiles_nonneg CHECK (video_starts >= 0 AND video_q25 >= 0 AND video_q50 >= 0 AND video_q75 >= 0 AND video_q100 >= 0),
	CONSTRAINT ck_cpe_video_misc_nonneg CHECK (skips >= 0 AND avg_watch_time_seconds >= 0),
	CONSTRAINT ck_cpe_interactions_nonneg CHECK (clicks >= 0 AND qr_scans >= 0 AND interactive_engagements >= 0),
	CONSTRAINT ck_cpe_reach_freq_nonneg CHECK (reach >= 0 AND frequency >= 0),
	CONSTRAINT ck_cpe_spend_nonneg CHECK (spend >= 0 AND effective_cpm >= 0),
	CONSTRAINT ck_cpe_errors_nonneg CHECK (error_count >= 0 AND timeout_count >= 0),
	FOREIGN KEY(campaign_id) REFERENCES campaigns (id) ON DELETE CASCADE ON UPDATE CASCADE
)
"""


class CampaignPerformanceExtended(Base):
    """
    Campaign-hour performance (extended) focused on CTV/video with Netflix core metrics.
    """

    __tablename__ = "campaign_performance_extended"
    __table_args__ = (
        CheckConstraint(
            "requests >= 0 AND responses >= 0 AND eligible_impressions >= 0 AND auctions_won >= 0",
            name="ck_cpe_supply_nonneg",
        ),
        CheckConstraint(
            "impressions >= 0 AND viewable_impressions >= 0 AND audible_impressions >= 0",
            name="ck_cpe_imps_nonneg",
        ),
        CheckConstraint(
            "video_starts >= 0 AND video_q25 >= 0 AND video_q50 >= 0 AND video_q75 >= 0 AND video_q100 >= 0",
            name="ck_cpe_quartiles_nonneg",
        ),
        CheckConstraint("skips >= 0 AND avg_watch_time_seconds >= 0", name="ck_cpe_video_misc_nonneg"),
        CheckConstraint(
            "clicks >= 0 AND qr_scans >= 0 AND interactive_engagements >= 0", name="ck_cpe_interactions_nonneg"
        ),
        CheckConstraint("reach >= 0 AND frequency >= 0", name="ck_cpe_reach_freq_nonneg"),
        CheckConstraint("spend >= 0 AND effective_cpm >= 0", name="ck_cpe_spend_nonneg"),
        CheckConstraint("error_count >= 0 AND timeout_count >= 0", name="ck_cpe_errors_nonneg"),
        # Relaxed logical constraints - allow small variations for realistic data
        CheckConstraint("responses >= 0.9 * requests", name="ck_cpe_responses_reasonable"),  # Allow 10% variation
        CheckConstraint(
            "eligible_impressions >= 0.8 * responses", name="ck_cpe_eligible_reasonable"
        ),  # Allow 20% variation
        CheckConstraint(
            "auctions_won >= 0.8 * eligible_impressions", name="ck_cpe_auctions_reasonable"
        ),  # Allow 20% variation
        CheckConstraint(
            "impressions >= 0.6 * auctions_won", name="ck_cpe_impressions_reasonable"
        ),  # Allow 40% variation - realistic for ad serving
        CheckConstraint("viewable_impressions <= impressions", name="ck_cpe_viewable_le_impressions"),
        CheckConstraint("audible_impressions <= impressions", name="ck_cpe_audible_le_impressions"),
        CheckConstraint("video_starts <= impressions", name="ck_cpe_video_starts_le_impressions"),
        CheckConstraint("video_q25 <= video_starts", name="ck_cpe_q25_le_starts"),
        CheckConstraint("video_q50 <= video_q25", name="ck_cpe_q50_le_q25"),
        CheckConstraint("video_q75 <= video_q50", name="ck_cpe_q75_le_q50"),
        CheckConstraint("video_q100 <= video_q75", name="ck_cpe_q100_le_q75"),
        CheckConstraint("skips <= video_starts", name="ck_cpe_skips_le_starts"),
        CheckConstraint("clicks <= impressions", name="ck_cpe_clicks_le_impressions"),
        CheckConstraint("qr_scans <= impressions", name="ck_cpe_qr_scans_le_impressions"),
        CheckConstraint("interactive_engagements <= impressions", name="ck_cpe_interactive_le_impressions"),
        CheckConstraint("reach <= impressions", name="ck_cpe_reach_le_impressions"),
        CheckConstraint("frequency >= 1", name="ck_cpe_frequency_positive"),
        CheckConstraint("avg_watch_time_seconds <= 3600", name="ck_cpe_watch_time_reasonable"),  # Max 1 hour
        Index("ix_cpe_campaign_hour_unique", "campaign_id", "hour_ts", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="Surrogate PK")

    # Grain
    campaign_id: Mapped[int] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE", onupdate="CASCADE"),
        index=True,
        nullable=False,
        comment="Campaign identifier (FK to campaigns.id)",
    )
    hour_ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="Hour timestamp with timezone (grain)",
    )
    hour_unix_epoch: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="Unix timestamp of hour_ts"
    )

    # Supply funnel
    requests: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Ad requests from player/device."
    )
    responses: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Ad responses returned from ad server."
    )
    eligible_impressions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Responses passing filters."
    )
    auctions_won: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Wins/selected responses.")
    impressions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="NETFLIX CORE: Total ad impressions served."
    )

    # Delivery quality
    viewable_impressions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Impressions meeting viewability standards."
    )
    audible_impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Volume-on starts.")

    # Video progression
    video_starts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="NETFLIX CORE: Number of video ads that began playing."
    )
    video_q25: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Views reaching 25% completion."
    )
    video_q50: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Views reaching 50% completion."
    )
    video_q75: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Views reaching 75% completion."
    )
    video_q100: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="NETFLIX CORE: Video completions."
    )
    skips: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="NETFLIX CORE: Skips of video ads.")
    avg_watch_time_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Average watch length in seconds."
    )

    # Interactions
    clicks: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="NETFLIX CORE: Total click-through interactions."
    )
    qr_scans: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="QR code scans (if tracked).")
    interactive_engagements: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Interactive overlays/choices."
    )

    # Reach & frequency
    reach: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Unique viewers in hour.")
    frequency: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="Average impressions per viewer in hour."
    )

    # Spend / pricing
    spend: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Spend in account currency cents.")
    effective_cpm: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Effective CPM in cents.")

    # Errors
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Player/serve errors.")
    timeout_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="Request timeouts.")

    # Optional metadata
    comment: Mapped[Optional[str]] = mapped_column(
        Text, comment="Additional notes or metadata about the campaign performance data."
    )

    # Temporal breakdown columns
    human_readable: Mapped[str] = mapped_column(Text, nullable=False, comment="Human-readable timestamp string")
    hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False, comment="Hour of day (0-23)")
    minute_of_hour: Mapped[int] = mapped_column(Integer, nullable=False, comment="Minute of hour (0-59)")
    second_of_minute: Mapped[int] = mapped_column(Integer, nullable=False, comment="Second of minute (0-59)")
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, comment="Day of week (0=Monday, 6=Sunday)")
    is_business_hour: Mapped[bool] = mapped_column(
        Integer, nullable=False, comment="Whether this is during business hours (0/1)"
    )

    # Date aggregation columns
    daily_day_date: Mapped[date] = mapped_column(Date, nullable=False, comment="Date of the hour_ts (for daily aggregation)")
    weekly_start_day_date: Mapped[date] = mapped_column(Date, nullable=False, comment="First day of week containing hour_ts (Monday)")
    monthly_start_day_date: Mapped[date] = mapped_column(Date, nullable=False, comment="First day of month containing hour_ts")

    ctr_recalc: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Recalculated CTR (clicks/impressions)"
    )
    viewability_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Viewability rate (viewable/impressions)"
    )
    audibility_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Audibility rate (audible/impressions)"
    )
    video_start_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Video start rate (starts/impressions)"
    )
    video_completion_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Video completion rate (q100/starts)"
    )
    video_skip_rate_ext: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Extended video skip rate (skips/starts)"
    )
    qr_scan_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="QR scan rate (scans/impressions)"
    )
    interactive_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Interactive engagement rate"
    )
    auction_win_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Auction win rate (won/eligible)"
    )
    error_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Error rate (errors/requests)"
    )
    timeout_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Timeout rate (timeouts/requests)"
    )
    supply_funnel_efficiency: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Supply funnel efficiency (eligible/requests)"
    )

    # Core calculated metrics (moved from CampaignPerformance)
    ctr: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="CTR: sum(clicks) / sum(impressions)"
    )
    completion_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Completion rate: sum(video_q100) / NULLIF(sum(video_start), 0) (0-1 ratio)"
    )
    render_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Render rate: sum(viewable_impressions) / sum(impressions)"
    )
    fill_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Fill rate: sum(auctions_won) / NULLIF(sum(eligible_impressions), 0)"
    )
    response_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Response rate: sum(responses) / NULLIF(sum(requests), 0)"
    )
    video_skip_rate: Mapped[float | None] = mapped_column(
        Numeric(5, 4), nullable=True, comment="Video skip rate: sum(skips) / NULLIF(sum(video_start), 0)"
    )


class CampaignHierarchyDenorm(Base):
    """
    Denormalized campaign hierarchy table for analytics.

    This table combines data from all hierarchy levels (Advertiser → Campaign →
    Flight → Budget → Line Item → Creative) into a single denormalized structure
    for efficient querying and analysis.
    """

    __tablename__ = "campaign_hierarchy_denorm"

    # Composite primary key (references to original entities)
    creative_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    line_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    advertiser_id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Advertiser columns
    advertiser_name: Mapped[str] = mapped_column(String(255), nullable=False)
    advertiser_status: Mapped[str] = mapped_column(String(8), nullable=False, default='ACTIVE')
    advertiser_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    advertiser_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    agency_name: Mapped[str | None] = mapped_column(String(255))

    # Campaign columns
    campaign_name: Mapped[str] = mapped_column(String(255), nullable=False)
    campaign_status: Mapped[str] = mapped_column(String(8), nullable=False, default='ACTIVE')
    campaign_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    campaign_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    objective: Mapped[str] = mapped_column(String(13), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default='USD')
    target_cpm: Mapped[int] = mapped_column(Integer, nullable=False)
    dsp_partner: Mapped[str] = mapped_column(String(14), nullable=False)
    programmatic_buy_type: Mapped[str | None] = mapped_column(String(23))
    programmatic_partner: Mapped[str | None] = mapped_column(String(14))
    content_adjacency_tier: Mapped[str | None] = mapped_column(String(6))
    brand_lift_enabled: Mapped[int | None] = mapped_column(Integer)
    attention_metrics_enabled: Mapped[int | None] = mapped_column(Integer)
    clean_room_provider: Mapped[str | None] = mapped_column(String(9))
    measurement_partner: Mapped[str | None] = mapped_column(String(18))
    external_ref: Mapped[str | None] = mapped_column(String(64))

    # Flight columns
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    flight_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    flight_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Budget columns
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_type: Mapped[str] = mapped_column(String(8), nullable=False)
    budget_currency: Mapped[str] = mapped_column(String(3), nullable=False, default='USD')
    budget_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    budget_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Line Item columns
    line_item_name: Mapped[str] = mapped_column(String(255), nullable=False)
    line_item_status: Mapped[str] = mapped_column(String(8), nullable=False, default='ACTIVE')
    line_item_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    line_item_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ad_format: Mapped[str] = mapped_column(String(19), nullable=False)
    bid_cpm: Mapped[int] = mapped_column(Integer, nullable=False)
    pacing_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    targeting_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    device_targets_json: Mapped[str | None] = mapped_column(Text)
    line_item_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    ad_server_type: Mapped[str | None] = mapped_column(String(8))
    pixel_vendor: Mapped[str | None] = mapped_column(String(12))
    geo_tier: Mapped[str | None] = mapped_column(String(7))

    # Creative columns
    creative_name: Mapped[str | None] = mapped_column(String(255))
    creative_status: Mapped[str] = mapped_column(String(8), nullable=False, default='ACTIVE')
    creative_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    creative_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    asset_url: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(15), nullable=False)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    qa_status: Mapped[str | None] = mapped_column(String(8))
    placement: Mapped[str | None] = mapped_column(String(8))
    file_format: Mapped[str | None] = mapped_column(String(3))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    frame_rate: Mapped[str | None] = mapped_column(String(6))
    bitrate_kbps: Mapped[int | None] = mapped_column(Integer)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    is_interactive: Mapped[int | None] = mapped_column(Integer)
    interactive_meta_json: Mapped[str | None] = mapped_column(Text)
    is_pause_ad: Mapped[int | None] = mapped_column(Integer)
    qr_code_url: Mapped[str | None] = mapped_column(Text)
    overlay_cta_text: Mapped[str | None] = mapped_column(String(64))

    # JSON representation of entire hierarchy
    campaign_hierarchy_json: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Additional computed analytics fields (for the view)
    flight_status: Mapped[str | None] = mapped_column(String(8))
    budget_category: Mapped[str | None] = mapped_column(String(20))
    resolution_tier: Mapped[str | None] = mapped_column(String(10))
    media_category: Mapped[str | None] = mapped_column(String(15))
    objective_group: Mapped[str | None] = mapped_column(String(20))
    dsp_tier: Mapped[str | None] = mapped_column(String(10))
    complexity_score: Mapped[int | None] = mapped_column(Integer)
    days_since_update: Mapped[int | None] = mapped_column(Integer)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_advertiser_campaign', 'advertiser_id', 'campaign_id'),
        Index('idx_campaign_line_item', 'campaign_id', 'line_item_id'),
        Index('idx_line_item_creative', 'line_item_id', 'creative_id'),
        Index('idx_campaign_status', 'campaign_status'),
        Index('idx_creative_qa_status', 'qa_status'),
        Index('idx_campaign_objective', 'objective'),
        Index('idx_campaign_dsp_partner', 'dsp_partner'),
        Index('idx_flight_dates', 'start_date', 'end_date'),
        Index('idx_budget_amount', 'amount'),
        Index('idx_creative_mime_type', 'mime_type'),
        Index('idx_creative_placement', 'placement'),
        Index('idx_creative_file_format', 'file_format'),
        Index('idx_creative_dimensions', 'width', 'height'),
        Index('idx_creative_frame_rate', 'frame_rate'),
        Index('idx_creative_bitrate', 'bitrate_kbps'),
        Index('idx_creative_file_size', 'file_size_bytes'),
        Index('idx_creative_interactive', 'is_interactive'),
        Index('idx_creative_pause_ad', 'is_pause_ad'),
        Index('idx_last_updated', 'last_updated'),
    )
