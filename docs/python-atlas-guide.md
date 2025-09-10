# Atlas + Spectator + Flask: Quick Guide

This repo provides the Atlas time-series stack along with Spectator client libraries. Below is a focused guide to use Atlas as an in‑memory time‑series DB with a processing engine and plotting, query it with Atlas Stack Language (ASL), publish metrics via Spectator (Python), and hit it from a simple Flask API.

## Overview

- Atlas: in‑memory time‑series database with a query engine and chart rendering API.
- ASL: Atlas Stack Language for expressing metric queries and transformations.
- Spectator: thin client for emitting metrics; Python client writes to a local SpectatorD agent.
- API: your Flask app emits counters/timers that flow into Atlas via SpectatorD.

Key docs in this repo:
- `docs/overview.md`
- `docs/asl/tutorial.md`
- `docs/api/graph/graph.md`
- `docs/spectator/index.md` and `docs/spectator/lang/py/usage.md`
- `docs/spectator/agent/usage.md` (SpectatorD agent)

## Data Flow

App (Flask, Spectator‑Py) → SpectatorD (UDP or UDS) → Atlas Aggregator → Atlas Graph/Query APIs

- Spectator‑Py default output is UDP `127.0.0.1:1234` to SpectatorD.
- SpectatorD batches and publishes to Atlas (configurable via `--uri`).

## Quickstart

### 1) Run Atlas Standalone (in‑memory)

Option A — download released jar (see `docs/getting-started.md`):

```
curl -LO https://github.com/Netflix/atlas/releases/download/v1.7.8/atlas-standalone-1.7.8.jar
java -jar atlas-standalone-1.7.8.jar
```

Option B — build from this repo (uses the existing Makefile):

```
make one-jar
java -jar target/standalone.jar
```

This starts Atlas with graph and tags APIs (default localhost on port 7101).

Verify:

```
curl -s 'http://localhost:7101/api/v1/tags' | head
```

### 2) Run SpectatorD (local metrics agent)

Install SpectatorD per `docs/spectator/agent/usage.md`, then run it pointing to Atlas:

```
spectatord --uri http://localhost:7101/api/v1/publish --verbose
```

Notes:
- Default UDP listen port is `1234`. Admin HTTP server is `1234/tcp`.
- For high‑volume local use, Unix Domain Socket is available via `--enable_socket`.

### 3) Run your Flask app (Spectator‑Py)

The Python example in `app.py` emits:
- `server.requestCount` (counter)
- `server.requestLatency` (timer)
- `server.responseSize` (distribution summary)

Run:

```
flask --app app run
```

Hit the API to generate traffic:

```
curl 'http://127.0.0.1:5000/api/v1/play?country=US&title=Demo'
```

If needed, override the Spectator output location (defaults to UDP localhost):

```
# examples: udp (default), unix socket, or disable
export SPECTATOR_OUTPUT_LOCATION='udp://127.0.0.1:1234'
# export SPECTATOR_OUTPUT_LOCATION='unix:///run/spectatord/spectatord.unix'
# export SPECTATOR_OUTPUT_LOCATION='none'
```

## Querying and Plotting with ASL

Open charts via the Graph API (`docs/api/graph/graph.md`). Example expressions:

- Total requests (sum):

```
http://localhost:7101/api/v1/graph?q=name,server.requestCount,:eq,:sum
```

- Filter to your endpoint path and status, then sum:

```
http://localhost:7101/api/v1/graph?q=name,server.requestCount,:eq,path,v1_play,:eq,:and,status,200,:eq,:and,:sum
```

- Average request latency:

```
http://localhost:7101/api/v1/graph?q=name,server.requestLatency,:eq,:avg
```

Explore tags to see what values are present:

```
http://localhost:7101/api/v1/tags
http://localhost:7101/api/v1/tags/name
```

See `docs/asl/tutorial.md` for more operators (e.g., `:by`, `:rolling-avg`, `:vspan`, etc.).

## Tips

- Spectator‑Py → SpectatorD is best‑effort; for batch jobs, ensure the process runs ≥5–10s so SpectatorD publishes (see `docs/spectator/lang/py/usage.md`).
- For testing without SpectatorD, use the Spectator‑Py `memory` writer: `Registry(Config('memory'))` and assert on lines captured.
- For synthetic data against Atlas, see `docs/getting-started.md` (use `publish-test.sh`).

## Files in this repo you’ll use

- Root `Makefile` target: `one-jar` builds `target/standalone.jar`.
- Python example: `app.py` (Flask + Spectator‑Py).
- Docs: `docs/overview.md`, `docs/asl/tutorial.md`, `docs/api/graph/graph.md`, `docs/spectator/lang/py/usage.md`, `docs/spectator/agent/usage.md`, `docs/getting-started.md`.
