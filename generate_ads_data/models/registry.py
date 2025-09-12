"""
Centralized registry for accessing all models, enums, constants, and schemas.

This registry provides a single point of access to all domain components,
making it easy to import and use models, schemas, and enums throughout the application.
"""

from __future__ import annotations

# Import all enums and constants
# Import utility functions
from .enums import (
    AdDuration,
    AdFormat,
    AdPlacement,
    AdServerType,
    AspectRatio,
    AudioChannels,
    AudioCodec,
    BudgetDefaults,
    BudgetType,
    CampaignDefaults,
    CampaignStatus,
    ChromaSubsampling,
    CleanRoomProvider,
    ColorPrimaries,
    ContentAdjacencyTier,
    CreativeDefaults,
    CreativeMimeType,
    Currency,
    Device,
    DspPartner,
    EntityStatus,
    EntityStatusStr,
    # Core enums
    EntityType,
    FileFormat,
    FrameRate,
    FrameRateMode,
    FreqCapScope,
    FreqCapUnit,
    GeoTier,
    InterestCategory,
    LifeStage,
    MeasurementPartner,
    Objective,
    PacingType,
    PixelVendor,
    # Default constants
    PricingDefaults,
    ProgrammaticBuyType,
    QAStatus,
    ResolutionTier,
    ScanType,
    ServingDefaults,
    TargetingDefaults,
    TargetingKey,
    TransferFunction,
    VideoCodecH264Profile,
    VideoCodecProresProfile,
    clamp_cpm_to_defaults,
    enum_check_column,
    is_valid_targeting_key,
)
from .enums import (
    status_column as reusable_status_column,
)

# Import all ORM models from orm.py
from .orm import (
    Advertiser,
    Base,
    Budget,
    Campaign,
    CampaignHierarchyDenorm,
    CampaignPerformance,
    CampaignPerformanceExtended,
    Creative,
    EntityBase,
    Flight,
    FrequencyCap,
    LineItem,
)

# Import all Pydantic schemas from schemas.py
from .schemas import (
    AdvertiserCreate,
    CampaignCreate,
    CreativeCreate,
    LineItemCreate,
    Targeting,
    CampaignHierarchyDenormSchema,
)
from .schemas import (
    Budget as BudgetSchema,
)
from .schemas import (
    Flight as FlightSchema,
)
from .schemas import (
    FrequencyCap as FrequencyCapSchema,
)


class EnumRegistry:
    """Registry for all enum classes and constants."""

    # Default constants
    PricingDefaults = PricingDefaults
    BudgetDefaults = BudgetDefaults
    CampaignDefaults = CampaignDefaults
    CreativeDefaults = CreativeDefaults
    TargetingDefaults = TargetingDefaults
    ServingDefaults = ServingDefaults

    # Core enums
    EntityType = EntityType
    EntityStatus = EntityStatus
    EntityStatusStr = EntityStatusStr
    Objective = Objective
    CampaignStatus = CampaignStatus
    AdFormat = AdFormat
    AdPlacement = AdPlacement
    BudgetType = BudgetType
    FreqCapUnit = FreqCapUnit
    FreqCapScope = FreqCapScope
    PacingType = PacingType
    QAStatus = QAStatus
    DspPartner = DspPartner
    ProgrammaticBuyType = ProgrammaticBuyType
    MeasurementPartner = MeasurementPartner
    CleanRoomProvider = CleanRoomProvider
    ContentAdjacencyTier = ContentAdjacencyTier
    Currency = Currency
    CreativeMimeType = CreativeMimeType
    FileFormat = FileFormat
    AdDuration = AdDuration
    FrameRate = FrameRate
    FrameRateMode = FrameRateMode
    ResolutionTier = ResolutionTier
    AspectRatio = AspectRatio
    ScanType = ScanType
    VideoCodecH264Profile = VideoCodecH264Profile
    VideoCodecProresProfile = VideoCodecProresProfile
    ChromaSubsampling = ChromaSubsampling
    ColorPrimaries = ColorPrimaries
    TransferFunction = TransferFunction
    AudioCodec = AudioCodec
    AudioChannels = AudioChannels
    AdServerType = AdServerType
    PixelVendor = PixelVendor
    Device = Device
    GeoTier = GeoTier
    LifeStage = LifeStage
    InterestCategory = InterestCategory
    TargetingKey = TargetingKey


class ORMRegistry:
    """Registry for all SQLAlchemy ORM models."""

    Base = Base
    EntityBase = EntityBase
    Advertiser = Advertiser
    Campaign = Campaign
    LineItem = LineItem
    Creative = Creative
    Flight = Flight
    Budget = Budget
    FrequencyCap = FrequencyCap
    CampaignPerformance = CampaignPerformance
    CampaignPerformanceExtended = CampaignPerformanceExtended
    CampaignHierarchyDenorm = CampaignHierarchyDenorm


class SchemaRegistry:
    """Registry for all Pydantic schemas."""

    # Create schemas
    AdvertiserCreate = AdvertiserCreate
    CampaignCreate = CampaignCreate
    LineItemCreate = LineItemCreate
    CreativeCreate = CreativeCreate

    # Common schemas
    FrequencyCapSchema = FrequencyCapSchema
    FlightSchema = FlightSchema
    BudgetSchema = BudgetSchema
    Targeting = Targeting

    # Denormalized schemas
    CampaignHierarchyDenormSchema = CampaignHierarchyDenormSchema


class UtilityRegistry:
    """Registry for utility functions and helpers."""

    is_valid_targeting_key = is_valid_targeting_key
    clamp_cpm_to_defaults = clamp_cpm_to_defaults
    enum_check_column = enum_check_column
    status_column = reusable_status_column


class Registry:
    """
    Main registry class that provides access to all domain components.

    This class consolidates all registries and provides convenient access
    to models, schemas, enums, and utilities through a single interface.
    """

    def __init__(self):
        self.enums = EnumRegistry()
        self.orm = ORMRegistry()
        self.schemas = SchemaRegistry()
        self.utils = UtilityRegistry()

    # Direct access properties for convenience
    @property
    def Base(self):
        return self.orm.Base

    @property
    def EntityBase(self):
        return self.orm.EntityBase

    @property
    def Advertiser(self):
        return self.orm.Advertiser

    @property
    def Campaign(self):
        return self.orm.Campaign

    @property
    def LineItem(self):
        return self.orm.LineItem

    @property
    def Creative(self):
        return self.orm.Creative

    @property
    def Flight(self):
        return self.orm.Flight

    @property
    def Budget(self):
        return self.orm.Budget

    @property
    def FrequencyCap(self):
        return self.orm.FrequencyCap

    @property
    def CampaignPerformance(self):
        return self.orm.CampaignPerformance

    @property
    def CampaignPerformanceExtended(self):
        return self.orm.CampaignPerformanceExtended

    @property
    def CampaignHierarchyDenorm(self):
        return self.orm.CampaignHierarchyDenorm

    @property
    def AdvertiserCreate(self):
        return self.schemas.AdvertiserCreate

    @property
    def CampaignCreate(self):
        return self.schemas.CampaignCreate

    @property
    def LineItemCreate(self):
        return self.schemas.LineItemCreate

    @property
    def CreativeCreate(self):
        return self.schemas.CreativeCreate

    @property
    def FrequencyCapSchema(self):
        return self.schemas.FrequencyCapSchema

    @property
    def FlightSchema(self):
        return self.schemas.FlightSchema

    @property
    def BudgetSchema(self):
        return self.schemas.BudgetSchema

    @property
    def Targeting(self):
        return self.schemas.Targeting

    @property
    def CampaignHierarchyDenormSchema(self):
        return self.schemas.CampaignHierarchyDenormSchema

    # Direct access to commonly used enums
    @property
    def BudgetType(self):
        return self.enums.BudgetType

    @property
    def CreativeMimeType(self):
        return self.enums.CreativeMimeType

    @property
    def TargetingKey(self):
        return self.enums.TargetingKey

    @property
    def EntityStatus(self):
        return self.enums.EntityStatus

    @property
    def EntityStatusStr(self):
        return self.enums.EntityStatusStr

    @property
    def Objective(self):
        return self.enums.Objective

    @property
    def QAStatus(self):
        return self.enums.QAStatus

    @property
    def AdFormat(self):
        return self.enums.AdFormat

    # Default constants
    @property
    def PricingDefaults(self):
        return self.enums.PricingDefaults

    @property
    def BudgetDefaults(self):
        return self.enums.BudgetDefaults

    @property
    def CampaignDefaults(self):
        return self.enums.CampaignDefaults

    @property
    def CreativeDefaults(self):
        return self.enums.CreativeDefaults

    @property
    def TargetingDefaults(self):
        return self.enums.TargetingDefaults


# Create a global registry instance
registry = Registry()

# Export the main components
__all__ = [
    "Registry",
    "registry",
    "EnumRegistry",
    "ORMRegistry",
    "SchemaRegistry",
    "UtilityRegistry",
    "CampaignHierarchyDenorm",
    "CampaignHierarchyDenormSchema",
]
