# FileDataSource (scaffolding)

Design 2: add a file-backed Database that plugs into the standard evaluator so ASL works unchanged.

Status: scaffolding only. Classes are present but loading logic is not implemented yet.

- Module: `atlas-core`
- Class: `com.netflix.atlas.core.db.FileDataSource`
- Registry: `com.netflix.atlas.core.db.DataSourceRegistry`

Usage (future):

- Create a Database for a local file URI:
  - `file:///path/to/data.csv?format=csv&step=60s&tz=UTC&map=name=metric,app=app`
  - `file:///path/to/data.json?format=v1`
  - `file:///path/to/data.json.gz?format=v2`

Goals:

- Map file columns to Atlas tags so `:eq`, `:and`, `:by` work.
- Respect `step`, `s`/`e`, and `tz` via `EvalContext`.
- Keep chart layer unchanged by reusing `Grapher` and `DefaultGraphEngine`.

Non-goals (for initial pass):

- Backend-specific operators requiring a live service.
- Performance tuning beyond small local files.

Next steps:

1. Implement CSV loader producing `TimeSeries` and `RoaringTagIndex`.
2. Implement JSON V1/V2 loaders (V1 = single-series graph JSON; V2 = JsonCodec GraphDef).
3. Add a small CLI/runner that builds a `Database` from `file://` and uses `Grapher` with `q=...`.

CSV schema and mapping

- Minimum columns:
  - `ts` (epoch millis or ISO-8601) and `value`.
  - Additional columns are treated as Atlas tags: `name`, `app`, `cluster`, etc.
- Mapping via URI `map=` parameter (comma-separated `k=v` pairs):
  - `ts=<col>`: timestamp column name (default `ts`).
  - `value=<col>`: value column name (default `value`).
  - `name=<col>`: column to copy into Atlas `name` tag.
  - `label=<col>`: optional display label override (stored as tag `atlas.label`).
  - `tag_prefix=<prefix>`: treat any column starting with `<prefix>` as a tag (e.g., `tag_nf.app`).
  - All other unmapped columns become tags as-is.
- Normalization:
  - Enforce fixed step grid `[s,e)` using `step` param; fill missing points with NaN.
  - Convert timestamps using `tz` and support both absolute (`s`,`e`) or relative windows.
  - Group rows into series by the full tag set (or a configured subset in the future).

JSON formats

- V1: structure like `atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json`:
  - Fields: `start`, `step`, `legend`, `metrics` (list of tag maps), `values` (list of list), etc.
  - Loader should merge `metrics` tags with values and produce one or more `TimeSeries`.
- V2: `JsonCodec`-encoded `GraphDef`; extract `plots.flatMap(_.lines.map(_.data))` to get `TimeSeries`.

Python models integration

- `GraphRequest` already mirrors Grapher’s query parameters and image flags.
- Local file flow:
  - Build `Database` via `DataSourceRegistry.forUri("file:///...?...map=...&step=60s&tz=UTC", config)`.
  - Build a URI from `GraphRequest.to_query_params()` (sets `q`, `s`, `e`, `tz`, `step`, etc.).
  - Call `Grapher.evalAndRender(uri, db)` and write with `DefaultGraphEngine`.
