"""
Domain enums and constants for the Netflix Ads model.

Notes:
- Project convention: All enum values should always be UPPER CASE.
- Centralized constants are the single source of truth for factories/validators.

Recommended improvements:
- Consider grouping constants into dataclasses for namespacing.
- Add validation helpers (e.g., is_valid_targeting_key) to reduce duplication.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum, IntEnum
from typing import Optional, Type

# SQLAlchemy helpers (used for reusable enum-backed columns)
from sqlalchemy import CheckConstraint, String, text  # type: ignore
from sqlalchemy.orm import Mapped, mapped_column  # type: ignore


@dataclass(frozen=True)
class PricingDefaults:
    DEFAULT_CPM_MIN: Decimal = Decimal("0.10")
    DEFAULT_CPM_MAX: Decimal = Decimal("50.00")
    DEFAULT_CPM_GAUSS_MEAN: Decimal = Decimal("25.00")
    DEFAULT_CPM_GAUSS_STDDEV: Decimal = Decimal("10.00")
    CPM_RANGE_USD: tuple[int, int] = (35, 65)
    MIN_QUARTERLY_INVESTMENT_USD: int = 500_000


@dataclass(frozen=True)
class BudgetDefaults:
    DEFAULT_BUDGET_MIN: Decimal = Decimal("10000")
    DEFAULT_BUDGET_MAX: Decimal = Decimal("100000")
    DECIMAL: Decimal = Decimal("0.01")


@dataclass(frozen=True)
class CampaignDefaults:
    DEFAULT_CAMPAIGN_START_OFFSET_DAYS: int = 1
    DEFAULT_CAMPAIGN_MIN_DURATION_DAYS: int = 14
    DEFAULT_CAMPAIGN_MAX_DURATION_DAYS: int = 56
    AD_LOAD_MINUTES_PER_HOUR: tuple[int, int] = (4, 5)


@dataclass(frozen=True)
class CreativeDefaults:
    ALLOWED_CREATIVE_DURATIONS: tuple[int, int] = (15, 30)
    DEFAULT_IMAGE_WIDTH: int = 1920
    DEFAULT_IMAGE_HEIGHT: int = 1080
    DEFAULT_RESOLUTION: tuple[int, int] = (1920, 1080)
    STANDARD_VIDEO_MAX_FILE_SIZE_MB: int = 500
    PAUSE_AD_MAX_FILE_SIZE_KB: int = 200
    INTERACTIVE_CTA_MAX_CHARS: int = 30
    INTERACTIVE_MIN_ZONE_PX: tuple[int, int] = (75, 75)
    SAFE_ZONE_SIDES_PX: int = 38
    SAFE_ZONE_TOP_BOTTOM_PX: int = 67
    H264_MIN_BITRATE_KBPS_720P: int = 8000
    H264_MIN_BITRATE_KBPS_1080P: int = 12000
    PRORES_MIN_BITRATE_KBPS_720P: int = 42000
    PRORES_MIN_BITRATE_KBPS_1080P: int = 80000
    CREATIVE_APPROVAL_SLA_HOURS: int = 48


@dataclass(frozen=True)
class TargetingDefaults:
    DEFAULT_AGE_RANGES: tuple[tuple[int, int], ...] = ((18, 24), (25, 34), (35, 44), (45, 54))


@dataclass(frozen=True)
class ServingDefaults:
    PACING_PCT_MIN: int = 1
    PACING_PCT_MAX: int = 100


class EntityType(IntEnum):
    advertiser = 1
    campaign = 2
    line_item = 3
    creative = 4


# dont delete, reference to sp amazon;
#     state                          TEXT NOT NULL CHECK (state IN ('ENABLED','PAUSED','ARCHIVED')
class EntityStatus(IntEnum):
    active = 1
    inactive = 2
    deleted = 3


class EntityStatusStr(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    DELETED = "DELETED"


class Objective(str, Enum):
    awareness = "AWARENESS"
    consideration = "CONSIDERATION"
    conversion = "CONVERSION"


class CampaignStatus(str, Enum):
    draft = "DRAFT"
    active = "ACTIVE"
    paused = "PAUSED"
    completed = "COMPLETED"


class AdFormat(str, Enum):
    standard_video = "STANDARD_VIDEO"
    interactive_overlay = "INTERACTIVE_OVERLAY"
    pause_ads = "PAUSE_ADS"
    binge_ads = "BINGE_ADS"
    sponsorship = "SPONSORSHIP"


class AdPlacement(str, Enum):
    PRE_ROLL = "PRE_ROLL"
    MID_ROLL = "MID_ROLL"
    LIVE = "LIVE"


class BudgetType(str, Enum):
    lifetime = "LIFETIME"
    daily = "DAILY"


class FreqCapUnit(str, Enum):
    day = "DAY"
    week = "WEEK"
    month = "MONTH"


class FreqCapScope(str, Enum):
    user = "USER"
    device = "DEVICE"
    campaign = "CAMPAIGN"


class PacingType(str, Enum):
    even = "EVEN"
    asap = "ASAP"


class QAStatus(str, Enum):
    pending = "PENDING"
    approved = "APPROVED"
    rejected = "REJECTED"


class DspPartner(str, Enum):
    dv360 = "DV360"  # legacy alias
    google_dv360 = "GOOGLE_DV360"
    the_trade_desk = "THE_TRADE_DESK"
    magnite = "MAGNITE"
    microsoft = "MICROSOFT"


class ProgrammaticBuyType(str, Enum):
    DIRECT_GUARANTEED = "DIRECT_GUARANTEED"
    PROGRAMMATIC_GUARANTEED = "PROGRAMMATIC_GUARANTEED"
    PROGRAMMATIC_PREFERRED = "PROGRAMMATIC_PREFERRED"
    PRIVATE_MARKETPLACE = "PRIVATE_MARKETPLACE"


class MeasurementPartner(str, Enum):
    NIELSEN = "NIELSEN"
    KANTAR = "KANTAR"
    LUCID = "LUCID"
    NCSOLUTIONS = "NCSOLUTIONS"
    AFFINITY_SOLUTIONS = "AFFINITY_SOLUTIONS"
    EDO = "EDO"


class CleanRoomProvider(str, Enum):
    SNOWFLAKE = "SNOWFLAKE"
    INFOSUM = "INFOSUM"
    LIVERAMP = "LIVERAMP"


class ContentAdjacencyTier(str, Enum):
    TIER_1 = "TIER_1"
    TIER_2 = "TIER_2"
    TIER_3 = "TIER_3"


class Currency(str, Enum):
    USD = "USD"


class CreativeMimeType(str, Enum):
    mp4 = "VIDEO/MP4"
    mov = "VIDEO/QUICKTIME"


class FileFormat(str, Enum):
    MP4 = "MP4"
    MOV = "MOV"


class AdDuration(IntEnum):
    s10 = 10
    s15 = 15
    s20 = 20
    s30 = 30
    s45 = 45
    s60 = 60
    s75 = 75


class FrameRate(str, Enum):
    R23_976 = "23_976"
    R24 = "24"
    R25 = "25"
    R29_97 = "29_97"
    R30 = "30"


class FrameRateMode(str, Enum):
    CONSTANT = "CONSTANT"


class ResolutionTier(str, Enum):
    HD_720P = "HD_720P"
    FHD_1080P = "FHD_1080P"
    UHD_4K = "UHD_4K"


class AspectRatio(str, Enum):
    R16_9 = "R16_9"


class ScanType(str, Enum):
    PROGRESSIVE = "PROGRESSIVE"


class VideoCodecH264Profile(str, Enum):
    BASELINE = "BASELINE"
    MAIN = "MAIN"
    HIGH = "HIGH"


class VideoCodecProresProfile(str, Enum):
    PRORES_422_HQ = "PRORES_422_HQ"
    PRORES_422 = "PRORES_422"
    PRORES_422_LT = "PRORES_422_LT"


class ChromaSubsampling(str, Enum):
    YUV_4_2_2 = "YUV_4_2_2"
    YUV_4_2_0 = "YUV_4_2_0"


class ColorPrimaries(str, Enum):
    BT_709 = "BT_709"


class TransferFunction(str, Enum):
    BT_709 = "BT_709"


class AudioCodec(str, Enum):
    PCM = "PCM"
    AAC_LC = "AAC_LC"


class AudioChannels(str, Enum):
    STEREO = "STEREO"
    SURROUND_5_1 = "SURROUND_5_1"


class AdServerType(str, Enum):
    VAST_TAG = "VAST_TAG"
    DSP_TAG = "DSP_TAG"


class PixelVendor(str, Enum):
    IAS = "IAS"
    DOUBLEVERIFY = "DOUBLEVERIFY"


class Device(str, Enum):
    DESKTOP = "DESKTOP"
    MOBILE = "MOBILE"
    CTV = "CTV"


class GeoTier(str, Enum):
    COUNTRY = "COUNTRY"
    REGION = "REGION"
    DMA = "DMA"
    CITY = "CITY"


class LifeStage(str, Enum):
    GENERAL = "GENERAL"


class InterestCategory(str, Enum):
    GENERAL = "GENERAL"


class TargetingKey(str, Enum):
    DEVICE = "DEVICE"
    GEO_COUNTRY = "GEO_COUNTRY"
    GEO_TIER = "GEO_TIER"
    CONTENT_GENRE = "CONTENT_GENRE"
    AGE_RANGE = "AGE_RANGE"
    GENDER = "GENDER"
    HOUSEHOLD_INCOME = "HOUSEHOLD_INCOME"
    LIFE_STAGE = "LIFE_STAGE"
    INTEREST_CATEGORY = "INTEREST_CATEGORY"


# Validation helpers
def is_valid_targeting_key(key: str) -> bool:
    return key in {k.value for k in TargetingKey}


def clamp_cpm_to_defaults(value: Decimal) -> Decimal:
    lower = PricingDefaults.DEFAULT_CPM_MIN
    upper = PricingDefaults.DEFAULT_CPM_MAX
    return max(lower, min(upper, value))


def is_allowed_creative_duration(seconds: int) -> bool:
    return seconds in CreativeDefaults.ALLOWED_CREATIVE_DURATIONS


### Generic column factory for any Enum defined in this module
def enum_check_column(
    enum_cls: Type[Enum],
    *,
    column_name: str,
    default: Optional[str] = None,
    length: Optional[int] = None,
    nullable: bool = False,
) -> Mapped[str]:
    values = [member.value for member in enum_cls]  # type: ignore[attr-defined]
    max_len = max((len(str(v)) for v in values), default=0)
    size = length or max_len or 1
    values_sql = ",".join(f"'{str(v)}'" for v in values)
    check_sql = f"{column_name} IN ({values_sql})"

    mapped_kwargs = {"nullable": nullable}
    if default is not None:
        mapped_kwargs["server_default"] = text(f"'{default}'")

    return mapped_column(
        String(size),
        CheckConstraint(check_sql),
        **mapped_kwargs,  # type: ignore[arg-type]
    )


def status_column() -> Mapped[str]:
    return enum_check_column(
        EntityStatusStr,
        column_name="status",
        default=EntityStatusStr.ACTIVE.value,
        length=8,
        nullable=False,
    )
