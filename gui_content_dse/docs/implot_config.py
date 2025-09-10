# implot_config.py  — Pydantic v2 scaffolding aligned with DearPyGui mvPlotting.*
from __future__ import annotations

from enum import IntEnum, IntFlag
from typing import List, Optional, Sequence, Tuple, Union, Dict, Any, Callable, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, field_validator, model_validator

# ---------- Basic types ----------
Color = Union[
    Tuple[int, int, int, int],
    Tuple[int, int, int],
    Tuple[float, float, float, float],
    Tuple[float, float, float],
]

# ---------- Core ImPlot-like enums ----------

class ImPlotMarker(IntEnum):
    NONE = 0
    CIRCLE = 1
    SQUARE = 2
    DIAMOND = 3
    UP = 4
    DOWN = 5
    LEFT = 6
    RIGHT = 7
    CROSS = 8
    PLUS = 9
    ASTERISK = 10

class ImPlotColormap(IntEnum):
    DEEP = 0; DARK = 1; PASTEL = 2; PAIRED = 3
    VIRIDIS = 4; PLASMA = 5; HOT = 6; COOL = 7
    PINK = 8; JET = 9; TWILIGHT = 10; RDBU = 11
    BRBG = 12; PIYG = 13; SPECTRAL = 14; GREYS = 15

class ImPlotScale(IntEnum):
    LINEAR = 0
    TIME = 1
    LOG10 = 2
    SYMLOG = 3

class PlotFlags(IntFlag):
    NONE = 0
    NO_TITLE = 1 << 0
    NO_LEGEND = 1 << 1
    NO_MOUSE_TEXT = 1 << 2
    NO_MENUS = 1 << 3
    NO_BOX_SELECT = 1 << 4
    NO_HIGHLIGHT = 1 << 5
    NO_CHILD = 1 << 6
    NO_FRAME = 1 << 7
    EQUAL = 1 << 8
    CROSSHAIRS = 1 << 9
    NO_INPUTS = 1 << 10
    # convenience: canvas-only composite
    CANVAS_ONLY = NO_TITLE | NO_LEGEND | NO_MENUS | NO_BOX_SELECT | NO_MOUSE_TEXT | NO_FRAME

class AxisFlags(IntFlag):
    NONE = 0
    NO_LABEL = 1 << 0
    NO_GRID_LINES = 1 << 1
    NO_TICK_MARKS = 1 << 2
    NO_TICK_LABELS = 1 << 3
    NO_MENUS = 1 << 4
    NO_SIDE_SWITCH = 1 << 5
    NO_HIGHLIGHT = 1 << 6
    OPPOSITE = 1 << 7
    FOREGROUND = 1 << 8
    INVERT = 1 << 9
    AUTO_FIT = 1 << 10
    RANGE_FIT = 1 << 11
    LOCK_MIN = 1 << 12
    LOCK_MAX = 1 << 13
    PAN_STRETCH = 1 << 14
    LOCK = LOCK_MIN | LOCK_MAX

class LineFlags(IntFlag):
    # FIX: LOOPS -> LOOP to match DPG setters【】
    NONE = 0
    LOOP = 1 << 0
    SEGMENTS = 1 << 1
    SHADED = 1 << 2
    NO_CLIP = 1 << 3
    SKIP_NAN = 1 << 4

class ScatterFlags(IntFlag):
    NONE = 0
    NO_CLIP = 1 << 0

class BarFlags(IntFlag):
    NONE = 0
    HORIZONTAL = 1 << 0

class BarGroupFlags(IntFlag):
    NONE = 0
    HORIZONTAL = 1 << 0
    STACKED = 1 << 1

class HistogramFlags(IntFlag):
    NONE = 0
    HORIZONTAL = 1 << 0
    CUMULATIVE = 1 << 1
    DENSITY = 1 << 2
    NO_OUTLIERS = 1 << 3
    COL_MAJOR = 1 << 4

class PieChartFlags(IntFlag):
    NONE = 0
    NORMALIZE = 1 << 0

class HeatmapFlags(IntFlag):
    NONE = 0
    COL_MAJOR = 1 << 0

class LegendFlags(IntFlag):
    NONE = 0
    HORIZONTAL = 1 << 0
    NO_HIGHLIGHT_AXIS = 1 << 1
    NO_HIGHLIGHT_ITEM = 1 << 2
    NO_MENUS = 1 << 3
    OUTSIDE = 1 << 4
    NO_BUTTONS = 1 << 5
    SORT = 1 << 6  # mirrors DPG legend flags mapping【】

class ImPlotLocation(IntEnum):
    CENTER = 0
    NORTH = 1
    SOUTH = 2
    WEST = 3
    EAST = 4
    NORTH_WEST = 5
    NORTH_EAST = 6
    SOUTH_WEST = 7
    SOUTH_EAST = 8

# ---------- Axis & Limits ----------

class AxisLimits(BaseModel):
    min: float
    max: float
    lock_min: bool = False
    lock_max: bool = False

    @model_validator(mode="after")
    def _validate_limits(self):
        if self.min > self.max:
            raise ValueError("AxisLimits: min must be <= max")
        return self

class AxisConfig(BaseModel):
    label: Optional[str] = None
    scale: ImPlotScale = ImPlotScale.LINEAR
    flags: AxisFlags = AxisFlags.NONE
    limits: Optional[AxisLimits] = None
    tick_labels: Optional[List[str]] = None
    tick_positions: Optional[List[float]] = None

    @model_validator(mode="after")
    def _tick_alignment(self):
        if self.tick_labels and self.tick_positions and len(self.tick_labels) != len(self.tick_positions):
            raise ValueError("AxisConfig: tick_labels and tick_positions length mismatch")
        return self

# ---------- Plot adornments / tools ----------

class LegendConfig(BaseModel):
    location: ImPlotLocation = ImPlotLocation.NORTH_WEST
    flags: LegendFlags = LegendFlags.NONE
    show: bool = True

class InputMapConfig(BaseModel):
    # matches fields DPG sets in draw_plot (pan/fit/select/menu/zoom + modifiers)【】
    pan: int = 0
    fit: int = 0
    select: int = 0
    select_cancel: int = 0
    menu: int = 0
    zoom_rate: float = 1.0
    pan_mod: int = 0
    select_mod: int = 0
    zoom_mod: int = 0
    override_mod: int = 0
    select_horz_mod: int = 0
    select_vert_mod: int = 0
    query_toggle_mod: int = 0

class QueryConfig(BaseModel):
    enabled: bool = False
    min_query_rects: int = 0
    max_query_rects: int = 0
    rects: List[Tuple[float, float, float, float]] = Field(default_factory=list)

# ---------- Base Series ----------

class SeriesBase(BaseModel):
    label: Optional[str] = None
    axis: int = Field(0, ge=0, le=2, description="Y-axis index (0..2)")
    color: Optional[Color] = None
    show: bool = True

# ---------- Concrete Series (aligned with mvPlotting.h) ----------

class LineSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]
    line_flags: LineFlags = LineFlags.NONE
    marker: ImPlotMarker = ImPlotMarker.NONE
    marker_size: float = Field(4.0, ge=0.0)
    line_weight: float = Field(1.0, ge=0.0)

    @field_validator("x", "y")
    @classmethod
    def _flt(cls, v: Sequence[float]) -> List[float]:
        return [float(t) for t in v]

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.x) != len(self.y):
            raise ValueError("LineSeriesConfig: x and y must be same length")
        return self

class ShadedSeriesConfig(SeriesBase):
    # (x, y1, y2); DPG will fill y2 with zeros if not provided【】
    x: Sequence[float]
    y1: Sequence[float]
    y2: Optional[Sequence[float]] = None

    @model_validator(mode="after")
    def _shape(self):
        if self.y2 is not None and len(self.y1) != len(self.y2):
            raise ValueError("ShadedSeriesConfig: y1 and y2 must match length")
        if len(self.x) != len(self.y1):
            raise ValueError("ShadedSeriesConfig: x and y1 length mismatch")
        return self

class ScatterSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]
    scatter_flags: ScatterFlags = ScatterFlags.NONE
    marker: ImPlotMarker = ImPlotMarker.CIRCLE
    marker_size: float = Field(4.0, ge=0.0)

    @field_validator("x", "y")
    @classmethod
    def _flt(cls, v: Sequence[float]) -> List[float]:
        return [float(t) for t in v]

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.x) != len(self.y):
            raise ValueError("ScatterSeriesConfig: x and y must be same length")
        return self

class StemSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]
    horizontal: bool = False  # DPG toggles ImPlotStemsFlags_Horizontal in C++【】

    @field_validator("x", "y")
    @classmethod
    def _flt(cls, v: Sequence[float]) -> List[float]:
        return [float(t) for t in v]

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.x) != len(self.y):
            raise ValueError("StemSeriesConfig: x and y must be same length")
        return self

class StairsSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.x) != len(self.y):
            raise ValueError("StairsSeriesConfig: x and y must be same length")
        return self

class InfLineSeriesConfig(SeriesBase):
    # DPG reads channel 0 for inf lines
    x: Sequence[float]

class BarSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]
    weight: float = Field(0.67, ge=0.0)
    bar_flags: BarFlags = BarFlags.NONE  # "horizontal" flag in C++【】

    @field_validator("x", "y")
    @classmethod
    def _flt(cls, v: Sequence[float]) -> List[float]:
        return [float(t) for t in v]

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.x) != len(self.y):
            raise ValueError("BarSeriesConfig: x and y must be same length")
        return self

class BarGroupSeriesConfig(SeriesBase):
    # DPG stores a flat values array + label_ids + group_size/width/shift + flags【】【】
    values: Sequence[float]
    label_ids: List[str]
    group_size: int = 1
    group_width: float = 0.67
    shift: int = 0
    flags: BarGroupFlags = BarGroupFlags.NONE

    @model_validator(mode="after")
    def _validate(self):
        if self.group_size <= 0:
            raise ValueError("BarGroupSeriesConfig: group_size must be >= 1")
        if len(self.values) % self.group_size != 0:
            raise ValueError("BarGroupSeriesConfig: len(values) must be a multiple of group_size")
        if len(self.label_ids) != self.group_size:
            raise ValueError("BarGroupSeriesConfig: label_ids length must equal group_size")
        return self

class HistogramSeriesConfig(SeriesBase):
    x: Sequence[float]
    bins: Optional[int] = Field(None, ge=1)
    bar_scale: float = Field(1.0, ge=0.0)
    min_range: Optional[float] = None
    max_range: Optional[float] = None
    histogram_flags: HistogramFlags = HistogramFlags.NONE

    @field_validator("x")
    @classmethod
    def _flt(cls, v: Sequence[float]) -> List[float]:
        return [float(t) for t in v]

class Histogram2DSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]
    xbins: int = -1
    ybins: int = -1
    xmin: float = 0.0
    xmax: float = 0.0
    ymin: float = 0.0
    ymax: float = 0.0
    flags: HistogramFlags = HistogramFlags.NONE

    @field_validator("x", "y")
    @classmethod
    def _flt(cls, v: Sequence[float]) -> List[float]:
        return [float(t) for t in v]

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.x) != len(self.y):
            raise ValueError("Histogram2DSeriesConfig: x and y must be same length")
        return self

class PieChartSeriesConfig(SeriesBase):
    values: Sequence[float]
    labels: Sequence[str]
    center: Tuple[float, float] = (0.0, 0.0)
    radius: float = Field(0.5, gt=0.0)
    angle0_deg: float = 90.0
    pie_flags: PieChartFlags = PieChartFlags.NONE
    format: Optional[str] = None

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.values) != len(self.labels):
            raise ValueError("PieChartSeriesConfig: values and labels length mismatch")
        return self

class HeatmapSeriesConfig(SeriesBase):
    z: Sequence[float]               # row-major unless COL_MAJOR flag set
    rows: int
    cols: int
    bounds_min: Tuple[float, float] = (0.0, 0.0)
    bounds_max: Tuple[float, float] = (1.0, 1.0)
    scale_min: float = 0.0
    scale_max: float = 1.0
    format: str = "%0.1f"
    flags: HeatmapFlags = HeatmapFlags.NONE

    @field_validator("z")
    @classmethod
    def _flt(cls, v: Sequence[float]) -> List[float]:
        return [float(t) for t in v]

    @model_validator(mode="after")
    def _shape(self):
        if self.rows * self.cols != len(self.z):
            raise ValueError("HeatmapSeriesConfig: z length must equal rows*cols")
        return self

class ErrorBarSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]
    negative: Sequence[float]
    positive: Sequence[float]
    horizontal: bool = False

    @model_validator(mode="after")
    def _len_check(self):
        n = len(self.x)
        if not (len(self.y) == len(self.negative) == len(self.positive) == n):
            raise ValueError("ErrorBarSeriesConfig: x,y,negative,positive must have equal length")
        return self

class CandleSeriesConfig(SeriesBase):
    dates: Sequence[float]  # epoch seconds or DPG time unit
    opens: Sequence[float]
    closes: Sequence[float]
    lows: Sequence[float]
    highs: Sequence[float]
    bull_color: Optional[Color] = None
    bear_color: Optional[Color] = None
    weight: float = 0.25
    tooltip: bool = True
    time_unit: int = 0  # ImPlotTimeUnit (e.g., Day)【】

    @model_validator(mode="after")
    def _len_check(self):
        n = len(self.dates)
        if not (len(self.opens) == len(self.closes) == len(self.lows) == len(self.highs) == n):
            raise ValueError("CandleSeriesConfig: arrays must have equal length")
        return self

class DigitalSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.x) != len(self.y):
            raise ValueError("DigitalSeriesConfig: x and y must be same length")
        return self

class LabelSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]
    labels: Sequence[str]
    offset: Tuple[float, float] = (0.0, 0.0)
    text_flags: int = 0  # ImPlotTextFlags

    @model_validator(mode="after")
    def _len_check(self):
        if not (len(self.x) == len(self.y) == len(self.labels)):
            raise ValueError("LabelSeriesConfig: x, y, and labels must be same length")
        return self

class ImageSeriesConfig(SeriesBase):
    texture_id: int
    bounds_min: Tuple[float, float]
    bounds_max: Tuple[float, float]
    uv_min: Tuple[float, float] = (0.0, 0.0)
    uv_max: Tuple[float, float] = (1.0, 1.0)
    tint: Tuple[float, float, float, float] = (1, 1, 1, 1)
    image_flags: int = 0  # ImPlotImageFlags

class AreaSeriesConfig(SeriesBase):
    x: Sequence[float]
    y: Sequence[float]
    fill: Color = (0, 0, 0, 0)

    @model_validator(mode="after")
    def _len_check(self):
        if len(self.x) != len(self.y):
            raise ValueError("AreaSeriesConfig: x and y must be same length")
        return self

class CustomSeriesConfig(SeriesBase):
    # DPG: channelCount 2..5 + tooltip + item flags【】
    channel_count: int = Field(2, ge=2, le=5)
    tooltip: bool = True
    item_flags: int = 0

SeriesConfig = Union[
    LineSeriesConfig,
    ShadedSeriesConfig,
    ScatterSeriesConfig,
    StemSeriesConfig,
    StairsSeriesConfig,
    InfLineSeriesConfig,
    BarSeriesConfig,
    BarGroupSeriesConfig,
    HistogramSeriesConfig,
    Histogram2DSeriesConfig,
    PieChartSeriesConfig,
    HeatmapSeriesConfig,
    ErrorBarSeriesConfig,
    CandleSeriesConfig,
    DigitalSeriesConfig,
    LabelSeriesConfig,
    ImageSeriesConfig,
    AreaSeriesConfig,
    CustomSeriesConfig,
]

# ---------- Plot Container ----------

class PlotThemeOverride(BaseModel):
    style_vars: List[Tuple[str, float]] = Field(default_factory=list)
    marker_override: Optional[ImPlotMarker] = None
    marker_size: Optional[float] = None
    line_weight: Optional[float] = None

class PlotConfig(BaseModel):
    title: Optional[str] = None
    x_axis: AxisConfig = AxisConfig(label="x")
    y_axes: List[AxisConfig] = Field(default_factory=lambda: [AxisConfig(label="y")])  # up to 3
    series: List[SeriesConfig] = Field(default_factory=list)

    plot_flags: PlotFlags = PlotFlags.NONE
    colormap: ImPlotColormap = ImPlotColormap.DEEP

    legend: LegendConfig = LegendConfig()
    input_map: Optional[InputMapConfig] = None
    query: Optional[QueryConfig] = None

    theme_tag: Optional[str] = None
    per_series_theme_tags: Optional[List[Optional[str]]] = None
    theme_override: Optional[PlotThemeOverride] = None

    @model_validator(mode="after")
    def _validate_axes(self):
        if not (1 <= len(self.y_axes) <= 3):
            raise ValueError("PlotConfig: y_axes must contain 1..3 axes")
        if self.per_series_theme_tags and len(self.per_series_theme_tags) != len(self.series):
            raise ValueError("PlotConfig: per_series_theme_tags length must match series")
        return self

# ---------- Theme Management ----------

class ThemeColor(BaseModel):
    """Individual color definition for themes"""
    name: str
    value: Color
    description: Optional[str] = None

class ThemeStyle(BaseModel):
    """Style variable for themes"""
    name: str
    value: float
    description: Optional[str] = None

class PlotTheme(BaseModel):
    """Complete theme definition for plots"""
    name: str
    description: Optional[str] = None
    colors: List[ThemeColor] = Field(default_factory=list)
    styles: List[ThemeStyle] = Field(default_factory=list)
    marker_override: Optional[ImPlotMarker] = None
    marker_size: Optional[float] = None
    line_weight: Optional[float] = None

class ThemeManager:
    """Manages plot themes and provides theme switching capabilities"""
    _themes: Dict[str, PlotTheme] = {}
    _current_theme: Optional[str] = None
    
    @classmethod
    def register_theme(cls, theme: PlotTheme) -> None:
        """Register a new theme"""
        cls._themes[theme.name] = theme
    
    @classmethod
    def get_theme(cls, name: str) -> Optional[PlotTheme]:
        """Get a theme by name"""
        return cls._themes.get(name)
    
    @classmethod
    def list_themes(cls) -> List[str]:
        """List all available theme names"""
        return list(cls._themes.keys())
    
    @classmethod
    def set_current_theme(cls, name: str) -> bool:
        """Set the current active theme"""
        if name in cls._themes:
            cls._current_theme = name
            return True
        return False
    
    @classmethod
    def get_current_theme(cls) -> Optional[PlotTheme]:
        """Get the current active theme"""
        if cls._current_theme:
            return cls._themes.get(cls._current_theme)
        return None

# ---------- Layout Management ----------

class WindowConfig(BaseModel):
    """Configuration for main application window"""
    title: str = "DearPyGUI Application"
    width: int = Field(1200, ge=100)
    height: int = Field(800, ge=100)
    resizable: bool = True
    always_on_top: bool = False
    maximized: bool = False
    fullscreen: bool = False

class DockSpaceConfig(BaseModel):
    """Configuration for dockable window spaces"""
    name: str
    width: float = 0.0  # 0.0 = auto-size
    height: float = 0.0  # 0.0 = auto-size
    split_ratio: float = 0.5
    split_direction: str = "horizontal"  # "horizontal" or "vertical"
    closable: bool = True
    movable: bool = True
    resizable: bool = True

class LayoutConfig(BaseModel):
    """Main layout configuration"""
    window: WindowConfig = WindowConfig()
    dock_spaces: List[DockSpaceConfig] = Field(default_factory=list)
    menu_bar: bool = True
    status_bar: bool = True
    tool_bar: bool = True

# ---------- Event System ----------

class EventType(IntEnum):
    """Types of events that can be dispatched"""
    PLOT_CLICK = 1
    PLOT_HOVER = 2
    PLOT_ZOOM = 3
    PLOT_PAN = 4
    SERIES_SELECT = 5
    AXIS_CHANGE = 6
    THEME_CHANGE = 7
    DATA_UPDATE = 8
    WINDOW_RESIZE = 9
    CUSTOM = 100

@dataclass
class Event:
    """Base event class"""
    type: EventType
    source: str
    data: Dict[str, Any]
    timestamp: float = 0.0

class EventHandler(Protocol):
    """Protocol for event handlers"""
    def handle(self, event: Event) -> None:
        """Handle an event"""
        ...

class EventDispatcher:
    """Manages event dispatching and handler registration"""
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._middleware: List[Callable[[Event], Event]] = []
    
    def register_handler(self, event_type: EventType, handler: EventHandler) -> None:
        """Register an event handler"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def add_middleware(self, middleware: Callable[[Event], Event]) -> None:
        """Add middleware to the event pipeline"""
        self._middleware.append(middleware)
    
    def dispatch(self, event: Event) -> None:
        """Dispatch an event to registered handlers"""
        # Apply middleware
        for middleware in self._middleware:
            event = middleware(event)
        
        # Dispatch to handlers
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                handler.handle(event)

# ---------- Data Binding and State Management ----------

class StateManager:
    """Manages application state and data binding"""
    def __init__(self):
        self._state: Dict[str, Any] = {}
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a state value and notify subscribers"""
        self._state[key] = value
        if key in self._subscribers:
            for callback in self._subscribers[key]:
                callback(value)
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a state value"""
        return self._state.get(key, default)
    
    def subscribe(self, key: str, callback: Callable[[Any], None]) -> None:
        """Subscribe to state changes"""
        if key not in self._subscribers:
            self._subscribers[key] = []
        self._subscribers[key].append(callback)
    
    def unsubscribe(self, key: str, callback: Callable[[Any], None]) -> None:
        """Unsubscribe from state changes"""
        if key in self._subscribers:
            self._subscribers[key].remove(callback)

class DataSource(ABC):
    """Abstract base class for data sources"""
    @abstractmethod
    def get_data(self) -> Any:
        """Get the current data"""
        pass
    
    @abstractmethod
    def subscribe(self, callback: Callable[[Any], None]) -> None:
        """Subscribe to data changes"""
        pass

class PlotDataSource(DataSource):
    """Data source specifically for plot data"""
    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        self._data = initial_data or {}
        self._subscribers: List[Callable[[Any], None]] = []
    
    def get_data(self) -> Dict[str, Any]:
        return self._data
    
    def update_data(self, key: str, value: Any) -> None:
        """Update a specific data key"""
        self._data[key] = value
        for callback in self._subscribers:
            callback(self._data)
    
    def subscribe(self, callback: Callable[[Any], None]) -> None:
        self._subscribers.append(callback)

# ---------- Widget Factory and Component Registry ----------

class WidgetConfig(BaseModel):
    """Base configuration for widgets"""
    id: str
    label: Optional[str] = None
    width: int = 0  # 0 = auto
    height: int = 0  # 0 = auto
    visible: bool = True
    enabled: bool = True
    tooltip: Optional[str] = None

class ComponentRegistry:
    """Registry for reusable UI components"""
    _components: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, component_class: type) -> None:
        """Register a component class"""
        cls._components[name] = component_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """Get a component class by name"""
        return cls._components.get(name)
    
    @classmethod
    def list_components(cls) -> List[str]:
        """List all registered component names"""
        return list(cls._components.keys())

class WidgetFactory:
    """Factory for creating widgets with proper configuration"""
    def __init__(self, registry: ComponentRegistry):
        self.registry = registry
    
    def create_widget(self, widget_type: str, config: WidgetConfig) -> Any:
        """Create a widget instance"""
        component_class = self.registry.get(widget_type)
        if component_class:
            return component_class(config)
        raise ValueError(f"Unknown widget type: {widget_type}")

# ---------- Validation and Error Handling ----------

class ValidationError(Exception):
    """Custom validation error with context"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value

class ConfigValidator:
    """Validates configuration objects and provides detailed error messages"""
    
    @staticmethod
    def validate_plot_config(config: PlotConfig) -> List[str]:
        """Validate a plot configuration and return error messages"""
        errors = []
        
        # Validate series data
        for i, series in enumerate(config.series):
            if hasattr(series, 'x') and hasattr(series, 'y'):
                if len(series.x) != len(series.y):
                    errors.append(f"Series {i}: x and y arrays must have equal length")
        
        # Validate axis configuration
        if len(config.y_axes) > 3:
            errors.append("Maximum 3 y-axes allowed")
        
        return errors
    
    @staticmethod
    def validate_theme(theme: PlotTheme) -> List[str]:
        """Validate a theme configuration"""
        errors = []
        
        if not theme.name:
            errors.append("Theme name cannot be empty")
        
        # Validate color values
        for color in theme.colors:
            if len(color.value) not in [3, 4]:
                errors.append(f"Color {color.name} must have 3 or 4 components")
        
        return errors

# ---------- Serialization and Persistence ----------

class ConfigSerializer:
    """Handles serialization and deserialization of configurations"""
    
    @staticmethod
    def to_dict(config: BaseModel) -> Dict[str, Any]:
        """Convert a configuration to a dictionary"""
        return config.model_dump()
    
    @staticmethod
    def from_dict(config_class: type, data: Dict[str, Any]) -> BaseModel:
        """Create a configuration from a dictionary"""
        return config_class.model_validate(data)
    
    @staticmethod
    def to_json(config: BaseModel, indent: int = 2) -> str:
        """Convert a configuration to JSON string"""
        return config.model_dump_json(indent=indent)
    
    @staticmethod
    def from_json(config_class: type, json_str: str) -> BaseModel:
        """Create a configuration from JSON string"""
        return config_class.model_validate_json(json_str)

class ConfigPersistence:
    """Manages saving and loading configurations"""
    def __init__(self, base_path: str = "./configs"):
        self.base_path = base_path
    
    def save_plot_config(self, name: str, config: PlotConfig) -> None:
        """Save a plot configuration to file"""
        import json
        import os
        
        os.makedirs(self.base_path, exist_ok=True)
        file_path = os.path.join(self.base_path, f"{name}_plot.json")
        
        with open(file_path, 'w') as f:
            json.dump(ConfigSerializer.to_dict(config), f, indent=2)
    
    def load_plot_config(self, name: str) -> Optional[PlotConfig]:
        """Load a plot configuration from file"""
        import json
        import os
        
        file_path = os.path.join(self.base_path, f"{name}_plot.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return ConfigSerializer.from_dict(PlotConfig, data)
        return None

# ---------- Application Controller Base ----------

class Controller(ABC):
    """Base class for application controllers following MVC pattern"""
    def __init__(self, event_dispatcher: EventDispatcher, state_manager: StateManager):
        self.event_dispatcher = event_dispatcher
        self.state_manager = state_manager
        self._setup_event_handlers()
    
    @abstractmethod
    def _setup_event_handlers(self) -> None:
        """Setup event handlers for this controller"""
        pass

class View(ABC):
    """Base class for DearPyGUI views"""
    def __init__(self, controller: Controller):
        self.controller = controller
    
    @abstractmethod
    def render(self) -> None:
        """Render the view using DearPyGUI"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup resources when view is destroyed"""
        pass

# ---------- Plugin System ----------

class TabSpec(BaseModel):
    """Specification for a tab plugin"""
    name: str
    display_name: str
    controller_class: str
    view_class: str
    description: Optional[str] = None
    version: str = "1.0.0"
    dependencies: List[str] = Field(default_factory=list)

class PluginRegistry:
    """Registry for managing plugins and tabs"""
    _tabs: Dict[str, TabSpec] = {}
    
    @classmethod
    def register_tab(cls, spec: TabSpec) -> None:
        """Register a tab specification"""
        cls._tabs[spec.name] = spec
    
    @classmethod
    def get_tab(cls, name: str) -> Optional[TabSpec]:
        """Get a tab specification by name"""
        return cls._tabs.get(name)
    
    @classmethod
    def list_tabs(cls) -> List[TabSpec]:
        """List all registered tabs"""
        return list(cls._tabs.values())

# ---------- Default Theme Definitions ----------

def create_default_themes() -> None:
    """Create and register default themes"""
    
    # Dark theme
    dark_theme = PlotTheme(
        name="dark",
        description="Dark theme with high contrast colors",
        colors=[
            ThemeColor(name="background", value=(0.1, 0.1, 0.1, 1.0), description="Plot background"),
            ThemeColor(name="grid", value=(0.3, 0.3, 0.3, 1.0), description="Grid lines"),
            ThemeColor(name="text", value=(0.9, 0.9, 0.9, 1.0), description="Text color"),
        ],
        styles=[
            ThemeStyle(name="LineWeight", value=2.0, description="Default line weight"),
            ThemeStyle(name="MarkerSize", value=6.0, description="Default marker size"),
        ]
    )
    ThemeManager.register_theme(dark_theme)
    
    # Light theme
    light_theme = PlotTheme(
        name="light",
        description="Light theme with clean appearance",
        colors=[
            ThemeColor(name="background", value=(1.0, 1.0, 1.0, 1.0), description="Plot background"),
            ThemeColor(name="grid", value=(0.7, 0.7, 0.7, 1.0), description="Grid lines"),
            ThemeColor(name="text", value=(0.1, 0.1, 0.1, 1.0), description="Text color"),
        ],
        styles=[
            ThemeStyle(name="LineWeight", value=1.5, description="Default line weight"),
            ThemeStyle(name="MarkerSize", value=5.0, description="Default marker size"),
        ]
    )
    ThemeManager.register_theme(light_theme)

# Initialize default themes
create_default_themes()
