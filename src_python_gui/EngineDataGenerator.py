#!/usr/bin/env python3
"""
EngineDataGenerator + Chart Model
---------------------------------

Python equivalent of Netflix Atlas EngineDataGenerator helpers and chart model
classes (ported from Scala/Java sources).

Includes:
- TimeSeries + EngineDataGenerator (synthetic data)
- Palette
- PlotBound
- DataDef (LineDef, HSpanDef, VSpanDef, MessageDef)
- PlotDef
- GraphDef
- HeatmapDef
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from enum import Enum, auto
from itertools import cycle

# ---------------------------------------------------------------------------
# Time Series + EngineDataGenerator
# ---------------------------------------------------------------------------


@dataclass
class TimeSeries:
    tags: dict[str, str]
    step_ms: int
    func: Callable[[int], float]
    label: str = "0"

    def data(self, t_ms: int) -> float:
        return self.func(t_ms)


class EngineDataGenerator:
    def __init__(self, step_ms: int = 60_000):
        self.step_ms = step_ms

    def constant(self, v: float, name: str | None = None) -> TimeSeries:
        return TimeSeries({"name": name or str(v)}, self.step_ms, lambda _: v)

    def wave(self, min_v: float, max_v: float, wavelength: timedelta) -> TimeSeries:
        lam = 2 * math.pi / wavelength.total_seconds() / 1000.0 * self.step_ms

        def f(t_ms: int) -> float:
            amp = (max_v - min_v) / 2.0
            yoffset = min_v + amp
            return amp * math.sin(t_ms * lam) + yoffset

        return TimeSeries({"name": "wave"}, self.step_ms, f)

    def interval(self, ts1: TimeSeries, ts2: TimeSeries, s_ms: int, e_ms: int) -> TimeSeries:
        def f(t_ms: int) -> float:
            ts = ts2 if s_ms <= t_ms < e_ms else ts1
            return ts.data(t_ms)

        return TimeSeries({"name": "interval"}, self.step_ms, f)

    def finegrain_wave(self, min_v: int, max_v: int, hours: int) -> TimeSeries:
        return self.wave(min_v, max_v, timedelta(hours=hours))

    def simple_wave(self, min_v: float = 0.0, max_v: float = 1.0) -> TimeSeries:
        return self.wave(min_v, max_v, timedelta(days=1))

    def outage_series(self, max_v: int) -> TimeSeries:
        start1 = datetime(2012, 1, 1, 5, 0, tzinfo=UTC)
        end1 = datetime(2012, 1, 1, 6, 38, tzinfo=UTC)
        start2 = datetime(2012, 1, 1, 7, 4, tzinfo=UTC)
        end2 = datetime(2012, 1, 1, 7, 5, tzinfo=UTC)

        bad = self.constant(0)
        normal = self.interval(
            self.simple_wave(0, max_v),
            bad,
            int(start1.timestamp() * 1000),
            int(end1.timestamp() * 1000),
        )
        return self.interval(normal, bad, int(start2.timestamp() * 1000), int(end2.timestamp() * 1000))

    def sample_series(self, ts: TimeSeries, start: datetime, end: datetime) -> list[float]:
        start_ms = int(start.timestamp() * 1000)
        end_ms = int(end.timestamp() * 1000)
        step = ts.step_ms
        return [ts.data(t) for t in range(start_ms, end_ms + 1, step)]


# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------


@dataclass
class Palette:
    name: str
    colors: list[tuple[int, int, int, int]]  # RGBA tuples

    def with_alpha(self, alpha: int) -> Palette:
        return Palette(self.name, [(r, g, b, alpha) for r, g, b, _ in self.colors])

    def as_grayscale(self) -> Palette:
        def to_gray(c):
            r, g, b, a = c
            v = int(0.21 * r + 0.72 * g + 0.07 * b)
            return (v, v, v, a)

        return Palette(f"grayscale_{self.name}", [to_gray(c) for c in self.colors])

    def __iter__(self):
        return cycle(self.colors)

    def color(self, i: int) -> tuple[int, int, int, int]:
        return self.colors[i % len(self.colors)]


Palette.DEFAULT = Palette(
    "default",
    [
        (255, 0, 0, 255),  # RED
        (0, 255, 0, 255),  # GREEN
        (0, 0, 255, 255),  # BLUE
        (255, 0, 255, 255),  # MAGENTA
        (255, 255, 0, 255),  # YELLOW
        (0, 255, 255, 255),  # CYAN
        (255, 192, 203, 255),  # PINK
        (255, 165, 0, 255),  # ORANGE
    ],
)


# ---------------------------------------------------------------------------
# PlotBound
# ---------------------------------------------------------------------------


class PlotBound:
    @staticmethod
    def auto_style():
        return "auto-style"

    @staticmethod
    def auto_data():
        return "auto-data"

    @staticmethod
    def explicit(v: float):
        return v


# ---------------------------------------------------------------------------
# DataDef (LineDef, HSpanDef, VSpanDef, MessageDef)
# ---------------------------------------------------------------------------


class LineStyle(Enum):
    LINE = auto()
    AREA = auto()
    STACK = auto()
    VSPAN = auto()
    HEATMAP = auto()


@dataclass
class DataDef:
    label: str
    color: tuple[int, int, int, int]


@dataclass
class LineDef(DataDef):
    data: TimeSeries = field(default=None)
    query: str | None = None
    group_by_keys: list[str] = field(default_factory=list)
    line_style: LineStyle = LineStyle.LINE
    line_width: float = 1.0

    def with_color(self, c: tuple[int, int, int, int]) -> LineDef:
        return replace(self, color=c)


@dataclass
class HSpanDef(DataDef):
    v1: float = 0.0
    v2: float = 0.0


@dataclass
class VSpanDef(DataDef):
    t1: datetime = field(default_factory=datetime.utcnow)
    t2: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MessageDef(DataDef):
    pass


# ---------------------------------------------------------------------------
# PlotDef
# ---------------------------------------------------------------------------


@dataclass
class PlotDef:
    data: list[DataDef]
    ylabel: str | None = None
    axis_color: tuple[int, int, int, int] | None = None
    scale: str = "linear"
    upper: str | float = PlotBound.auto_style()
    lower: str | float = PlotBound.auto_style()
    heatmap: HeatmapDef | None = None


# ---------------------------------------------------------------------------
# GraphDef
# ---------------------------------------------------------------------------


@dataclass
class GraphDef:
    plots: list[PlotDef]
    start_time: datetime
    end_time: datetime
    step: int = 60_000
    width: int = 400
    height: int = 200
    layout: str = "canvas"
    zoom: float = 1.0
    title: str | None = None
    legend_type: str = "labels_with_stats"
    only_graph: bool = False
    warnings: list[str] = field(default_factory=list)
    theme_name: str = "light"

    def adjust_plots(self, f: Callable[[PlotDef], PlotDef]) -> GraphDef:
        return replace(self, plots=[f(p) for p in self.plots])

    def adjust_lines(self, f: Callable[[LineDef], LineDef]) -> GraphDef:
        new_plots = []
        for p in self.plots:
            new_data = [f(d) if isinstance(d, LineDef) else d for d in p.data]
            new_plots.append(replace(p, data=new_data))
        return replace(self, plots=new_plots)


# ---------------------------------------------------------------------------
# HeatmapDef
# ---------------------------------------------------------------------------


@dataclass
class HeatmapDef:
    color_scale: str = "linear"
    upper: str | float = PlotBound.auto_data()
    lower: str | float = PlotBound.auto_data()
    palette: Palette | None = None
    label: str | None = None
