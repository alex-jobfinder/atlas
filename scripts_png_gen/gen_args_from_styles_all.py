#!/usr/bin/env python3

import os
import re
import sys
import json
from urllib.parse import urlparse, parse_qsl, unquote_plus
from pathlib import Path
from typing import Dict, List, Tuple

"""
to run: 
python3 scripts_png_gen/gen_args_from_styles_all.py
"""

INPUT_PATH = "/home/alex/dbt_ads/atlas/scripts_png_gen/styles_all/styles_all.txt"
OUTPUT_BASE = "/home/alex/dbt_ads/atlas/scripts_png_gen/styles_all/args"
PNG_BASE = "/home/alex/dbt_ads/atlas/scripts_png_gen/output/styles_all"

SUPPORTED_PARAMS = {
    "q", "s", "e", "tz", "step", "theme", "layout", "w", "h", "palette", "no_legend"
}


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "group"


def dedent_api_line(line: str) -> str:
    return line.strip()


def parse_api_query(line: str) -> Dict[str, List[str]]:
    # Expect lines like: /api/v1/graph?param=value&param2=value
    try:
        qpos = line.index('?')
    except ValueError:
        return {}
    query = line[qpos + 1 :].strip()
    # parse_qsl preserves order; keep duplicates by grouping values in lists
    pairs = parse_qsl(query, keep_blank_values=True)
    params: Dict[str, List[str]] = {}
    for k, v in pairs:
        params.setdefault(k, []).append(v)
    return params


def pick_first(params: Dict[str, List[str]], key: str) -> str:
    vals = params.get(key)
    return vals[0] if vals else ""


def needs_alerts_preset(q_value: str, group_path: str) -> bool:
    q_lower = q_value.lower()
    if "alerttest" in q_lower:
        return True
    if "/asl/alerting-expressions" in group_path:
        return True
    return False


def build_args_line(group_slug: str, idx: int, params: Dict[str, List[str]], group_path: str) -> Tuple[str, str, str]:
    # Determine preset
    raw_q = pick_first(params, "q")
    # Decode q using unquote_plus to convert '+' to spaces, '%XX' to chars
    q_value = unquote_plus(raw_q) if raw_q else ""

    preset = "alerts" if needs_alerts_preset(q_value, group_path) else "sps"

    # Recognized params mapping
    s = pick_first(params, "s")
    e = pick_first(params, "e")
    tz = pick_first(params, "tz")
    step = pick_first(params, "step")
    theme = pick_first(params, "theme") or "light"
    layout = pick_first(params, "layout")
    w = pick_first(params, "w") or "700"
    h = pick_first(params, "h") or "300"
    palette = pick_first(params, "palette")

    no_legend_vals = params.get("no_legend")
    no_legend_flag = (no_legend_vals and any(v in ("1", "true", "True") for v in no_legend_vals))

    # If stack=1 in query and q does not already contain :stack, append via --style
    style = None
    stack_vals = params.get("stack")
    if stack_vals and any(v in ("1", "true", "True") for v in stack_vals):
        if q_value and ":stack" not in q_value:
            style = "stack"

    # Compose OUT paths
    base_name = f"{group_slug}_{idx:03d}"
    png_dir = os.path.join(PNG_BASE, group_slug)
    out_png = os.path.join(png_dir, f"{base_name}.png")
    out_v2 = os.path.join(png_dir, f"{base_name}.v2.json.gz")

    # Build args parts
    parts: List[str] = []
    parts.append(f"--preset {preset}")
    if q_value:
        # Escape embedded quotes
        q_escaped = q_value.replace('"', '\\"')
        parts.append(f"--q \"{q_escaped}\"")
    if s:
        parts.append(f"--s {s}")
    if e:
        parts.append(f"--e {e}")
    if tz:
        parts.append(f"--tz {tz}")
    if step:
        parts.append(f"--step {step}")
    if no_legend_flag:
        parts.append("--no-legend")
    if theme:
        parts.append(f"--theme {theme}")
    if layout:
        parts.append(f"--layout {layout}")
    if w:
        parts.append(f"--w {w}")
    if h:
        parts.append(f"--h {h}")
    if palette:
        parts.append(f"--palette {palette}")
    if style:
        parts.append(f"--style {style}")

    parts.append(f"--out {out_png}")
    parts.append(f"--emit-v2 {out_v2}")

    return " ".join(parts), out_png, out_v2


def main(input_path: str = INPUT_PATH, output_base: str = OUTPUT_BASE) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    group_path = None
    group_slug = None
    group_index = 0

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("## "):
            group_path = stripped[3:].strip()
            group_slug = slugify(group_path)
            group_index = 0
            # Prepare directories
            out_dir = os.path.join(output_base, group_slug)
            png_dir = os.path.join(PNG_BASE, group_slug)
            os.makedirs(out_dir, exist_ok=True)
            os.makedirs(png_dir, exist_ok=True)
            continue
        if not stripped.startswith("/api/v1/graph"):
            # Skip non-API lines
            continue
        if not group_slug:
            # If no group header seen yet, put in a generic group
            group_path = "misc"
            group_slug = slugify(group_path)
            group_index = 0
            os.makedirs(os.path.join(output_base, group_slug), exist_ok=True)
            os.makedirs(os.path.join(PNG_BASE, group_slug), exist_ok=True)

        group_index += 1
        params = parse_api_query(stripped)
        args_line, out_png, out_v2 = build_args_line(group_slug, group_index, params, group_path or "")

        out_dir = os.path.join(output_base, group_slug)
        args_filename = os.path.join(out_dir, f"{group_slug}_{group_index:03d}.args")
        with open(args_filename, "w", encoding="utf-8") as af:
            af.write(args_line)

    print(f"Generated args under: {output_base}")


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else INPUT_PATH
    out_base = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_BASE
    main(in_path, out_base)
