from __future__ import annotations

import argparse
from pathlib import Path

from .atlas_chart import GraphQuery, build_graph_url, fetch_chart


def main() -> int:
    p = argparse.ArgumentParser(description="Fetch a line chart PNG from Atlas Graph API")
    p.add_argument("--base-url", default="http://localhost:7101", help="Atlas base URL")
    p.add_argument("--expr", required=True, help="ASL expression for q=")
    p.add_argument("--window", default="e-1h", help="Time window start, e.g. e-1h (maps to s=)")
    p.add_argument("--end", default=None, help="Optional end time (maps to e=)")
    p.add_argument("--step", default=None, help="Optional step, e.g. 1m")
    p.add_argument("--no-legend", action="store_true", help="Hide legend")
    p.add_argument("--out", default="chart.png", help="Output PNG path")

    args = p.parse_args()

    extra = {}
    if args.no_legend:
        extra["no_legend"] = "1"

    q = GraphQuery(expr=args.expr, start=args.window, end=args.end, step=args.step, params=extra)
    url = build_graph_url(args.base_url, q)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fetch_chart(url, str(out_path))

    print(f"Saved chart to {out_path} from {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
