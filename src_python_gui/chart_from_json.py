# from __future__ import annotations

# import argparse
# import json
# import math
# from dataclasses import dataclass
# from datetime import UTC
# from pathlib import Path

# from PIL import Image, ImageDraw

# from .atlas_graph_models import GraphRequest, Theme
# from .EngineDataGenerator import EngineDataGenerator, Palette


# @dataclass
# class Series:
#     label: str
#     values: list[float]


# def _load_v1_json(path: str) -> tuple[int, int, list[Series]]:
#     """Load the simple V1-style JSON used in atlas-chart test resources.

#     Expected keys: start (ms), step (ms), legend (labels), values (list[list]).
#     Returns: (start_ms, step_ms, list of Series)
#     """
#     with open(path, encoding="utf-8") as f:
#         data = json.load(f)

#     start = int(data["start"])  # epoch ms
#     step = int(data["step"])  # ms

#     labels: list[str] = data.get("legend") or ["series"] * len(data.get("values", []))
#     values_raw: list[list[float]] = data.get("values", [])

#     series: list[Series] = []
#     for i, vals in enumerate(values_raw):
#         label = labels[i] if i < len(labels) else f"series_{i}"
#         # Flatten 1-element inner lists if present
#         flat: list[float] = [v[0] if isinstance(v, list) and v else float("nan") for v in vals]
#         series.append(Series(label=label, values=flat))

#     return start, step, series


# def _theme_colors(theme: Theme) -> dict:
#     if theme == Theme.DARK:
#         return {
#             "bg": (24, 24, 24, 255),
#             "fg": (220, 220, 220, 255),
#             "axis": (160, 160, 160, 255),
#             "grid": (70, 70, 70, 255),
#         }
#     return {
#         "bg": (255, 255, 255, 255),
#         "fg": (0, 0, 0, 255),
#         "axis": (80, 80, 80, 255),
#         "grid": (220, 220, 220, 255),
#     }


# def _compute_y_range(series: list[Series]) -> tuple[float, float]:
#     vals: list[float] = []
#     for s in series:
#         for v in s.values:
#             if v is None:
#                 continue
#             try:
#                 x = float(v)
#                 if math.isnan(x) or math.isinf(x):
#                     continue
#                 vals.append(x)
#             except Exception:
#                 continue

#     if not vals:
#         return 0.0, 1.0
#     lo, hi = min(vals), max(vals)
#     if lo == hi:
#         # widen tiny range
#         pad = (abs(hi) if hi != 0 else 1.0) * 0.1
#         return hi - pad, hi + pad
#     return lo, hi


# def _draw_axes(draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, color_axis, color_grid):
#     # Border box
#     draw.rectangle([x0, y0, x1, y1], outline=color_axis)
#     # Horizontal grid lines (4)
#     h = y1 - y0
#     for i in range(1, 4):
#         y = y0 + (h * i) // 4
#         draw.line([(x0, y), (x1, y)], fill=color_grid)


# def _plot_series(
#     draw: ImageDraw.ImageDraw, s: Series, color, x0: int, y0: int, x1: int, y1: int, y_min: float, y_max: float
# ):
#     w = x1 - x0
#     n = len(s.values)
#     if n <= 1 or y_max <= y_min:
#         return

#     # Map idx -> x position across the width, inclusive
#     # Avoid overlapping last pixel by using (n - 1) segments
#     def to_xy(i: int, v: float) -> tuple[int, int]:
#         x = x0 + int(round((w * i) / (n - 1)))
#         # invert y for image coordinates
#         y = y1 - int(round((v - y_min) / (y_max - y_min) * (y1 - y0)))
#         return x, y

#     prev_xy: tuple[int, int] | None = None
#     for i, v in enumerate(s.values):
#         if v is None:
#             prev_xy = None
#             continue
#         try:
#             val = float(v)
#             if math.isnan(val) or math.isinf(val):
#                 prev_xy = None
#                 continue
#         except Exception:
#             prev_xy = None
#             continue
#         xy = to_xy(i, val)
#         if prev_xy is not None:
#             draw.line([prev_xy, xy], fill=color, width=2)
#         prev_xy = xy


# def render_chart_from_json(
#     input_json: str,
#     output_png: str,
#     request: GraphRequest | None = None,
#     overlay_wave: bool = False,
#     style: str = "line",
#     axis_groups: list[int] | None = None,
#     ylabel_left: str | None = None,
#     ylabel_right: str | None = None,
# ):
#     """Render a very simple line chart PNG from a local V1-style JSON.

#     - Uses EngineDataGenerator.Palette for line colors.
#     - Honors Theme via GraphRequest.theme (light/dark background), width/height if provided.
#     - Optionally overlays a generated wave using EngineDataGenerator to exercise helpers.
#     """
#     req = request or GraphRequest(q="local-file")
#     theme = req.theme or Theme.LIGHT
#     colors = _theme_colors(theme)

#     start_ms, step_ms, series = _load_v1_json(input_json)

#     # Optionally overlay a synthetic wave (demonstrates EngineDataGenerator usage)
#     if overlay_wave:
#         gen = EngineDataGenerator(step_ms=step_ms)
#         ts = gen.simple_wave(0, 1)
#         # sample for length of first series or 300 points if none
#         n = len(series[0].values) if series else 300
#         # start/end based on start_ms and n
#         from datetime import datetime, timedelta

#         start = datetime.fromtimestamp(start_ms / 1000, tz=UTC)
#         end = start + timedelta(milliseconds=step_ms * (n - 1))
#         vals = gen.sample_series(ts, start, end)
#         series.append(Series(label="synthetic-wave", values=vals))

#     # Canvas
#     width = req.w or 700
#     height = req.h or 200
#     img = Image.new("RGBA", (width, height), color=colors["bg"])
#     draw = ImageDraw.Draw(img)

#     # Plot area margins
#     left = 48
#     right = 16
#     top = 8
#     bottom = 24
#     x0, y0 = left, top
#     x1, y1 = width - right, height - bottom

#     _draw_axes(draw, x0, y0, x1, y1, colors["axis"], colors["grid"])

#     # Axis grouping
#     if axis_groups is None or len(axis_groups) != len(series):
#         axis_groups = [0] * len(series)

#     axes: dict[int, list[Series]] = {}
#     for s, ax in zip(series, axis_groups, strict=False):
#         axes.setdefault(ax, []).append(s)

#     supported_axes = sorted(axes.keys())[:2]  # 0 -> left, 1 -> right

#     # Compute ranges per axis; for stack, compute over stacked sums
#     def _stacked_range(ss: list[Series]) -> tuple[float, float]:
#         if not ss:
#             return (0.0, 1.0)
#         n = max(len(s.values) for s in ss)
#         totals: list[float] = []
#         for i in range(n):
#             total = 0.0
#             for s in ss:
#                 v = s.values[i] if i < len(s.values) else float("nan")
#                 try:
#                     fv = float(v)
#                     if not (fv == fv and fv not in (float("inf"), float("-inf"))):
#                         fv = 0.0
#                 except Exception:
#                     fv = 0.0
#                 total += fv
#             totals.append(total)
#         lo, hi = (min(totals), max(totals)) if totals else (0.0, 1.0)
#         if lo == hi:
#             pad = (abs(hi) if hi != 0 else 1.0) * 0.1
#             return hi - pad, hi + pad
#         return lo, hi

#     y_ranges: dict[int, tuple[float, float]] = {}
#     for ax in supported_axes:
#         ss = axes.get(ax, [])
#         y_ranges[ax] = _stacked_range(ss) if style == "stack" else _compute_y_range(ss)

#     # Axis labels (simple top placement)
#     if ylabel_left:
#         draw.text((4, 2), ylabel_left, fill=colors["fg"])  # left label
#     if ylabel_right:
#         draw.text((max(x1 - 100, x0 + 5), 2), ylabel_right, fill=colors["fg"])  # right label

#     def ymap(ax: int, v: float) -> int:
#         ymin, ymax = y_ranges.get(ax, (0.0, 1.0))
#         if ymax <= ymin:
#             return (y0 + y1) // 2
#         return y1 - int(round((v - ymin) / (ymax - ymin) * (y1 - y0)))

#     pal = Palette.DEFAULT

#     def draw_line(ss: list[Series], ax: int) -> None:
#         for i, s in enumerate(ss):
#             r, g, b, _ = pal.color(i)
#             _plot_series(draw, s, (r, g, b, 255), x0, y0, x1, y1, y_ranges[ax][0], y_ranges[ax][1])

#     def draw_area(ss: list[Series], ax: int) -> None:
#         for i, s in enumerate(ss):
#             r, g, b, _ = pal.color(i)
#             n = len(s.values)
#             if n <= 1:
#                 continue
#             ymin, ymax = y_ranges[ax]
#             baseline = 0.0 if ymin <= 0.0 <= ymax else ymin
#             pts: list[tuple[int, int]] = []
#             for idx, v in enumerate(s.values):
#                 try:
#                     fv = float(v)
#                 except Exception:
#                     fv = float("nan")
#                 if fv != fv or fv in (float("inf"), float("-inf")):
#                     continue
#                 x = x0 + int(round((x1 - x0) * idx / max(1, n - 1)))
#                 pts.append((x, ymap(ax, fv)))
#             if len(pts) < 2:
#                 continue
#             base_pts = [(x, ymap(ax, baseline)) for (x, _) in reversed(pts)]
#             draw.polygon(pts + base_pts, fill=(r, g, b, 100))
#             draw.line(pts, fill=(r, g, b, 255), width=2)

#     def draw_stack(ss: list[Series], ax: int) -> None:
#         if not ss:
#             return
#         n = max(len(s.values) for s in ss)
#         base = [0.0] * n
#         for i, s in enumerate(ss):
#             r, g, b, _ = pal.color(i)
#             top: list[float] = []
#             for idx in range(n):
#                 v = s.values[idx] if idx < len(s.values) else float("nan")
#                 try:
#                     fv = float(v)
#                 except Exception:
#                     fv = float("nan")
#                 if fv != fv or fv in (float("inf"), float("-inf")):
#                     fv = 0.0
#                 top.append(base[idx] + fv)
#             pts_top = []
#             pts_base = []
#             for idx in range(n):
#                 x = x0 + int(round((x1 - x0) * idx / max(1, n - 1)))
#                 pts_top.append((x, ymap(ax, top[idx])))
#                 pts_base.append((x, ymap(ax, base[idx])))
#             draw.polygon(pts_top + list(reversed(pts_base)), fill=(r, g, b, 110))
#             draw.line(pts_top, fill=(r, g, b, 255), width=2)
#             base = top

#     for ax in supported_axes:
#         ss = axes.get(ax, [])
#         if style == "area":
#             draw_area(ss, ax)
#         elif style == "stack":
#             draw_stack(ss, ax)
#         else:
#             draw_line(ss, ax)

#     out = Path(output_png)
#     out.parent.mkdir(parents=True, exist_ok=True)
#     img.save(out, format="PNG")


# def main() -> int:
#     p = argparse.ArgumentParser(description="Render a simple PNG chart from an Atlas test JSON (local file)")
#     p.add_argument("--input", "-i", required=True, help="Path to V1-style graph JSON")
#     p.add_argument("--output", "-o", required=True, help="Output PNG path")
#     p.add_argument("--theme", choices=["light", "dark"], default="light", help="Chart theme")
#     p.add_argument("--width", type=int, default=700, help="Image width")
#     p.add_argument("--height", type=int, default=200, help="Image height")
#     p.add_argument("--overlay-wave", action="store_true", help="Overlay a synthetic wave series")
#     p.add_argument("--style", choices=["line", "area", "stack"], default="line", help="Line style for series")
#     p.add_argument(
#         "--axis-groups",
#         default=None,
#         help="Comma-separated axis index per series (e.g., '0,1,0'). Only axes 0 (left) and 1 (right) are drawn",
#     )
#     p.add_argument("--ylabel-left", default=None, help="Left Y-axis label")
#     p.add_argument("--ylabel-right", default=None, help="Right Y-axis label")

#     args = p.parse_args()
#     req = GraphRequest(
#         q="local-file",
#         theme=Theme.DARK if args.theme == "dark" else Theme.LIGHT,
#         w=args.width,
#         h=args.height,
#     )
#     axis_groups = None
#     if args.axis_groups:
#         axis_groups = [int(x.strip()) for x in args.axis_groups.split(",") if x.strip()]
#     render_chart_from_json(
#         args.input,
#         args.output,
#         req,
#         overlay_wave=args.overlay_wave,
#         style=args.style,
#         axis_groups=axis_groups,
#         ylabel_left=args.ylabel_left,
#         ylabel_right=args.ylabel_right,
#     )
#     print(f"Saved PNG to {args.output}")
#     return 0


# if __name__ == "__main__":
#     raise SystemExit(main())
