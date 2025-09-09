from __future__ import annotations

from collections.abc import Mapping
from enum import Enum
from typing import Literal, Union

from pydantic import BaseModel, Field

# =============================
# Enums for Graph API parameters
# =============================


class OutputFormat(str, Enum):
    PNG = "png"
    CSV = "csv"
    TXT = "txt"
    JSON = "json"
    STD_JSON = "std.json"
    STATS_JSON = "stats.json"


class LayoutMode(str, Enum):
    CANVAS = "canvas"
    IMAGE = "image"
    IMAGE_WIDTH = "iw"
    IMAGE_HEIGHT = "ih"


class AxisScale(str, Enum):
    LINEAR = "linear"
    LOG = "log"
    LOG_LINEAR = "log-linear"
    POW2 = "pow2"
    SQRT = "sqrt"


class TickLabelsMode(str, Enum):
    DECIMAL = "decimal"
    BINARY = "binary"
    DURATION = "duration"
    OFF = "off"


class SortMode(str, Enum):
    LEGEND = "legend"
    MIN = "min"
    MAX = "max"
    AVG = "avg"
    COUNT = "count"
    TOTAL = "total"
    LAST = "last"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class VisionType(str, Enum):
    NORMAL = "normal"
    PROTANOPIA = "protanopia"
    PROTANOMALY = "protanomaly"
    DEUTERANOPIA = "deuteranopia"
    DEUTERANOMALY = "deuteranomaly"
    TRITANOPIA = "tritanopia"
    TRITANOMALY = "tritanomaly"
    ACHROMATOPSIA = "achromatopsia"
    ACHROMATOMALY = "achromatomaly"


class Theme(str, Enum):
    LIGHT = "light"
    DARK = "dark"


class LineStyle(str, Enum):
    LINE = "line"
    AREA = "area"
    STACK = "stack"
    VERTICAL_SPAN = "vspan"
    HEATMAP = "heatmap"


class PaletteName(str, Enum):
    ARMYTAGE = "armytage"
    DARK24 = "dark24"
    LIGHT24 = "light24"
    EPIC = "epic"
    BLUES = "blues"
    GREENS = "greens"
    ORANGES = "oranges"
    PURPLES = "purples"
    REDS = "reds"


# =============================
# Helper data types
# =============================


# Axis bounds can be a float or special automatic values.
AxisBound = Union[float, Literal["auto-style", "auto-data"]]


def _bool_flag(value: bool | None) -> str | None:
    if value is None:
        return None
    return "1" if value else "0"


def _format_hex_color_list(hex_colors: list[str]) -> str:
    # Atlas expects ASL list syntax e.g. "(,ff0000,00ff00,0000ff,)"
    # Accept colors either with or without leading '#', strip '#'.
    parts = [c.lstrip("#") for c in hex_colors]
    return "(," + ",".join(parts) + ",)"


class PaletteSelection(BaseModel):
    """Represents the palette selection for lines/axes.

    Options:
    - name: one of the built-in palette names
    - hashed: if true, prefix with "hash:" (e.g., "hash:armytage")
    - custom: explicit list of hex colors (mutually exclusive with name)
    """

    name: PaletteName | None = None
    hashed: bool = False
    custom: list[str] | None = None

    def as_query_value(self) -> str | None:
        if self.custom:
            return _format_hex_color_list(self.custom)
        if self.name:
            base = self.name.value
            return f"hash:{base}" if self.hashed else base
        return None


class HeatmapOptions(BaseModel):
    heatmap_l: float | None = Field(default=None, description="Lower bound for heatmap cell counts")
    heatmap_u: float | None = Field(default=None, description="Upper bound for heatmap cell counts")
    heatmap_palette: PaletteSelection | None = None
    heatmap_label: str | None = None
    heatmap_scale: AxisScale | None = None

    def to_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        if self.heatmap_l is not None:
            params["heatmap_l"] = str(self.heatmap_l)
        if self.heatmap_u is not None:
            params["heatmap_u"] = str(self.heatmap_u)
        if self.heatmap_palette is not None:
            value = self.heatmap_palette.as_query_value()
            if value:
                params["heatmap_palette"] = value
        if self.heatmap_label:
            params["heatmap_label"] = self.heatmap_label
        if self.heatmap_scale is not None:
            params["heatmap_scale"] = self.heatmap_scale.value
        return params


class AxisOverrides(BaseModel):
    """Per-axis overrides such as bounds or palette, addressed by axis index.

    Use zero-based axis indices (0 = left axis, 1..N = additional axes).
    """

    lower_bounds: Mapping[int, AxisBound] = Field(
        default_factory=dict, description="Map of axis index to lower bound (l.<i>)"
    )
    upper_bounds: Mapping[int, AxisBound] = Field(
        default_factory=dict, description="Map of axis index to upper bound (u.<i>)"
    )
    palettes: Mapping[int, PaletteSelection] = Field(
        default_factory=dict, description="Map of axis index to palette (palette.<i>)"
    )

    def to_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {}
        for idx, bound in self.lower_bounds.items():
            params[f"l.{idx}"] = str(bound)
        for idx, bound in self.upper_bounds.items():
            params[f"u.{idx}"] = str(bound)
        for idx, pal in self.palettes.items():
            value = pal.as_query_value()
            if value:
                params[f"palette.{idx}"] = value
        return params


# =============================
# Main Graph Request Model
# =============================


class GraphRequest(BaseModel):
    # Data / Query
    q: str = Field(..., description="Atlas Stack Language (ASL) expression")
    step: str | None = Field(default=None, description="Deprecated step size (duration)")

    # Time parameters
    s: str | None = Field(default=None, description="Start time (absolute/relative)")
    e: str | None = Field(default=None, description="End time (absolute/relative)")
    tz: str | None = Field(default=None, description="Time zone ID, e.g., 'UTC' or 'US/Pacific'")

    # Image flags
    title: str | None = None
    no_legend: bool | None = None
    no_legend_stats: bool | None = None
    axis_per_line: bool | None = None
    only_graph: bool | None = None
    vision: VisionType | None = None

    # Image size / layout
    layout: LayoutMode | None = None
    w: int | None = None
    h: int | None = None
    zoom: float | None = None

    # Y-Axis
    stack: bool | None = Field(default=None, description="Default line style is stack when true")
    l: AxisBound | None = None
    u: AxisBound | None = None
    ylabel: str | None = None
    palette: PaletteSelection | None = None
    scale: AxisScale | None = None
    tick_labels: TickLabelsMode | None = None
    sort: SortMode | None = None
    order: SortOrder | None = None

    # Output
    format: OutputFormat | None = None
    callback: str | None = None

    # Theme
    theme: Theme | None = None

    # Heatmap-specific options (apply when using :heatmap line style in ASL)
    heatmap: HeatmapOptions | None = None

    # Multi-Y axis overrides
    axis_overrides: AxisOverrides | None = None

    def to_query_params(self) -> dict[str, str]:
        params: dict[str, str] = {}

        # Required
        params["q"] = self.q

        # Time
        if self.s:
            params["s"] = self.s
        if self.e:
            params["e"] = self.e
        if self.tz:
            params["tz"] = self.tz
        if self.step:
            params["step"] = self.step

        # Image flags
        if self.title:
            params["title"] = self.title
        val = _bool_flag(self.no_legend)
        if val is not None:
            params["no_legend"] = val
        val = _bool_flag(self.no_legend_stats)
        if val is not None:
            params["no_legend_stats"] = val
        val = _bool_flag(self.axis_per_line)
        if val is not None:
            params["axis_per_line"] = val
        val = _bool_flag(self.only_graph)
        if val is not None:
            params["only_graph"] = val
        if self.vision is not None:
            params["vision"] = self.vision.value

        # Layout
        if self.layout is not None:
            params["layout"] = self.layout.value
        if self.w is not None:
            params["w"] = str(self.w)
        if self.h is not None:
            params["h"] = str(self.h)
        if self.zoom is not None:
            params["zoom"] = str(self.zoom)

        # Y-Axis
        val = _bool_flag(self.stack)
        if val is not None:
            params["stack"] = val
        if self.l is not None:
            params["l"] = str(self.l)
        if self.u is not None:
            params["u"] = str(self.u)
        if self.ylabel:
            params["ylabel"] = self.ylabel
        if self.palette is not None:
            pal_value = self.palette.as_query_value()
            if pal_value:
                params["palette"] = pal_value
        if self.scale is not None:
            params["scale"] = self.scale.value
        if self.tick_labels is not None:
            params["tick_labels"] = self.tick_labels.value
        if self.sort is not None:
            params["sort"] = self.sort.value
        if self.order is not None:
            params["order"] = self.order.value

        # Output
        if self.format is not None:
            params["format"] = self.format.value
        if self.callback:
            params["callback"] = self.callback

        # Theme
        if self.theme is not None:
            params["theme"] = self.theme.value

        # Heatmap
        if self.heatmap is not None:
            params.update(self.heatmap.to_query_params())

        # Multi-Y Axis overrides
        if self.axis_overrides is not None:
            params.update(self.axis_overrides.to_query_params())

        return params


def build_graph_url(base_url: str, request: GraphRequest) -> str:
    """Create a full /api/v1/graph URL with encoded query parameters.

    Example:
        build_graph_url("https://atlas/api/v1/graph", GraphRequest(q="name,sps,:eq"))
    """

    from urllib.parse import urlencode

    query = urlencode(request.to_query_params(), doseq=True)
    if "?" in base_url:
        return f"{base_url}&{query}" if not base_url.endswith("?") else f"{base_url}{query}"
    return f"{base_url}?{query}"


__all__ = [
    "AxisBound",
    "AxisOverrides",
    "AxisScale",
    "GraphRequest",
    "HeatmapOptions",
    "LayoutMode",
    "LineStyle",
    "OutputFormat",
    "PaletteName",
    "PaletteSelection",
    "SortMode",
    "SortOrder",
    "Theme",
    "TickLabelsMode",
    "VisionType",
    "build_graph_url",
]


## EXAMPLE USAGE DONT DELETE
"""
from atlas.atlas_graph_models import (
    GraphRequest, OutputFormat, LayoutMode, AxisScale, TickLabelsMode,
    SortMode, SortOrder, PaletteSelection, PaletteName, Theme, build_graph_url
)

req = GraphRequest(
    q="name,sps,:eq,(,nf.cluster,),:by",
    s="e-3h",
    e="now",
    tz="UTC",
    layout=LayoutMode.CANVAS,
    w=700,
    h=300,
    tick_labels=TickLabelsMode.DECIMAL,
    scale=AxisScale.LINEAR,
    sort=SortMode.MAX,
    order=SortOrder.DESC,
    palette=PaletteSelection(name=PaletteName.ARMYTAGE),
    format=OutputFormat.PNG,
    theme=Theme.LIGHT,
)
url = build_graph_url("https://atlas.example.com/api/v1/graph", req)
# -> https://atlas.example.com/api/v1/graph?q=...&w=700&h=300&format=png

"""
