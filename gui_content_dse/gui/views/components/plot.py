from __future__ import annotations

from typing import List
import dearpygui.dearpygui as dpg


def set_time_ticks(x_axis: int, xs: List[float], index_labels: List[str], plot_width: int, sidebar_width: int = 320):
    if not xs:
        return
    try:
        # Budget ~110 px per label
        px_per_label = 110
        avail = plot_width if plot_width > 0 else max(600, dpg.get_viewport_client_width() - sidebar_width - 40)
        max_ticks = max(2, min(12, avail // px_per_label))
        n = len(xs)
        step = max(1, (n + max_ticks - 1) // max_ticks)
        tick_positions = [xs[i] for i in range(0, n, step)]
        labels: List[str] = []
        for pos in tick_positions:
            i = int(pos)
            labels.append(index_labels[i] if 0 <= i < len(index_labels) else str(i))
        ticks = list(zip(tick_positions, labels))
        if hasattr(dpg, "set_axis_ticks"):
            dpg.set_axis_ticks(x_axis, ticks)
    except Exception:
        pass

