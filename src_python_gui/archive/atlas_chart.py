from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlencode, urljoin

import requests


@dataclass(frozen=True)
class GraphQuery:
    expr: str
    start: str | None = None  # e.g., "e-1h" or ISO8601
    end: str | None = None  # e.g., "e" or ISO8601
    step: str | None = None  # e.g., "1m"
    params: dict[str, str] | None = None  # extra URL params


def build_graph_url(base_url: str, query: GraphQuery) -> str:
    """Construct an Atlas Graph API URL for a PNG chart.

    base_url: e.g., "http://localhost:7101" (no trailing slash required)
    query.expr: ASL expression, e.g., "name,server.requestCount,:eq,:sum"
    query.start: start time (e.g., "e-1h")
    query.end: end time (default None lets server use 'now')
    query.step: step size (e.g., "1m")
    query.params: additional key/value pairs (e.g., {"no_legend": "1"})
    """
    base = base_url.rstrip("/") + "/"
    path = "api/v1/graph"

    qs: dict[str, str] = {"q": query.expr}
    if query.start:
        # Atlas expects 's' for start
        qs["s"] = query.start
    if query.end:
        # Atlas expects 'e' for end
        qs["e"] = query.end
    if query.step:
        qs["step"] = query.step
    if query.params:
        qs.update(query.params)

    return urljoin(base, path) + "?" + urlencode(qs)


def fetch_chart(url: str, out_path: str, timeout: float = 10.0) -> None:
    """Fetch a chart PNG from Atlas and write it to out_path.

    Raises requests.HTTPError for non-200 responses.
    """
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)
