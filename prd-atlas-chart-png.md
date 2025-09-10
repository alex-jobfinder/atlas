# PRD: Generate PNG Charts from atlas-chart Tests

## Overview
- Goal: Provide a reliable, documented way to run an existing `atlas-chart` test with bundled example data and produce a `.png` chart artifact.
- Outcome: Engineers can run a targeted test and retrieve a generated PNG from the `atlas-chart` module `target/` directory (plus an HTML diff report when applicable).

## Background
- The `atlas-chart` module contains comprehensive rendering tests. Many tests render a chart as a PNG and compare it to blessed “golden” images in the repo.
- Rendering assertions are mediated by `GraphAssertions` which, for cross-platform consistency, only enables comparisons and artifact writing when the font/rendering environment matches expected settings (`Fonts.shouldRunTests`).
- Example data for tests is stored in resources, e.g.:
  - `atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json`
- A representative test class that renders PNGs is `DefaultGraphEngineSuite`, which extends `PngGraphEngineSuite` and uses the “default” graph engine.

## Users
- Internal engineers and contributors who need to verify chart rendering or generate example artifacts for documentation and validation.

## In Scope
- Identify and document how to run an existing `atlas-chart` test that emits a `.png` file using bundled example data.
- Provide concrete commands and output locations.

## Out of Scope (for now)
- Creating new tests or modifying rendering logic.
- Changing font gating or image blessing mechanics.
- Building a standalone CLI for rendering charts from JSON (see Future Work).

## Constraints and Assumptions
- Java/SBT build is used. Commands assume `sbt` is available via `project/sbt` wrapper or on `PATH`.
- PNG emission in test runs is gated by font environment to ensure deterministic diffs. Current gating requires JDK ≥ 15 on macOS (arm64) to write images and diffs during tests (see `atlas-chart/src/main/scala/com/netflix/atlas/chart/util/Fonts.scala:54`). On other systems, assertions short‑circuit and images may not be written.
- Headless AWT is acceptable for image rendering; pass `-Djava.awt.headless=true` as needed.

## Success Metrics
- A documented, repeatable command that runs a specific test and, in a compatible environment, produces a `.png` in `atlas-chart/target/DefaultGraphEngineSuite/`.
- Clear runbook notes for environments where the gated assertions prevent artifact writing.

## Milestones and Tasks

1) Identify how to run an existing test to produce a PNG (First Task)
- Test target: `com.netflix.atlas.chart.DefaultGraphEngineSuite` → test name: `non_uniformly_drawn_spikes`.
- Example data: `atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json`.
- Command (from repo root):
  - Using the repo’s sbt wrapper:
    - `project/sbt 'project atlas-chart' 'testOnly com.netflix.atlas.chart.DefaultGraphEngineSuite -- -z non_uniformly_drawn_spikes' -Djava.awt.headless=true`
  - Or with system sbt:
    - `sbt 'project atlas-chart' 'testOnly com.netflix.atlas.chart.DefaultGraphEngineSuite -- -z non_uniformly_drawn_spikes' -Djava.awt.headless=true`
- Expected outputs (in compatible font environment):
  - PNGs written to: `atlas-chart/target/DefaultGraphEngineSuite/`
    - `default_non_uniformly_drawn_spikes.png`
    - `dark_default_non_uniformly_drawn_spikes.png`
  - Diff report (if diffs exist) and index: `atlas-chart/target/DefaultGraphEngineSuite/report.html`
- Notes on environment:
  - If running on non‑macOS or non‑arm64, or JDK < 15, `Fonts.shouldRunTests` returns false and `GraphAssertions.assertEquals(...)` returns early. In that case, images and diffs will not be written by tests. The test will still execute (and validate JSON round‑trip), but no files are emitted.

Acceptance Criteria
- The runbook commands above are verified in a compatible environment to produce the expected PNG(s) under `atlas-chart/target/DefaultGraphEngineSuite/`.
- If running on an incompatible environment, the PRD clearly states that images may not be emitted due to font gating and points to Future Work for cross‑platform PNG generation.

2) Document prerequisites and environment setup
- Ensure JDK ≥ 17 is installed and selected (recommended; ≥ 15 required by gating).
- On macOS ARM64: set `JAVA_HOME` to JDK ≥ 17, install `sbt`, and run the command above.
- Optional: confirm headless mode with `-Djava.awt.headless=true` if running without a GUI session.

3) Future Work (Optional follow‑ups)
- Added a small runnable entry point (`ChartRenderRunner`) that reads a graph JSON (V1 test JSON or V2 `JsonCodec` JSON, optionally `.gz`) and writes a PNG using `DefaultGraphEngine`, bypassing font-gated assertions. This enables PNG creation on any platform:
  - Input: path to JSON (e.g., `default_non_uniformly_drawn_spikes.json`).
  - Output: path to PNG file.
  - Location: `atlas-chart/src/main/scala/...` with `sbt 'project atlas-chart' run` support.
- Introduce a test flag or system property to allow writing artifacts even when font gating is disabled (only for local development, not CI).
- Provide a Docker image with a compatible JDK/macos-like rendering setup (if feasible) for deterministic artifact generation.

### Runner Usage
- Render the bundled sample (V1 JSON) to a PNG:
  - `sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json --output target/manual/default_non_uniformly_drawn_spikes.png'`
- Render a V2 JsonCodec JSON (plain or `.gz`):
  - `sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input <path-to-json-or-json.gz> --format v2 --output target/manual/out.png'`

## Dependencies
- SBT/Scala toolchain (already in repo via `project/sbt`).
- JDK ≥ 15 for deterministic rendering in tests (≥ 17 recommended).

## Risks
- Cross-platform rendering inconsistencies lead to flaky diffs or disabled artifact writes on most developer machines.
- Developer confusion if test runs “pass” but emit no images on incompatible environments.

## Deliverables
- This PRD and a runbook to execute `DefaultGraphEngineSuite` for `non_uniformly_drawn_spikes` to produce PNGs.
- Clear environment notes and a roadmap for a platform-independent PNG rendering runner.


## Local Python Graphing (No Server / No Atlas In‑Memory DB)

- **Goal**: Recreate chart rendering locally in Python using Pydantic models/enums instead of HTTP, consuming existing Atlas test data files directly and producing PNG artifacts without starting Atlas or using its in‑memory DB.

- **Use existing test data**:
  - Directory: `atlas-chart/src/test/resources/graphengine/data/`
  - Examples:
    - V1 JSON: `default_non_uniformly_drawn_spikes.json`
    - V2 JsonCodec (gz): e.g., `heatmap_basic.json.gz`, `heatmap_basic_negative.json.gz`, etc.

atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json
atlas-chart/src/test/resources/graphengine/data/heatmap_basic_negative.json.gz
atlas-chart/src/test/resources/graphengine/data/heatmap_basic.json.gz
atlas-chart/src/test/resources/graphengine/data/heatmap_dist.json.gz
atlas-chart/src/test/resources/graphengine/data/heatmap_timer_overlay.json.gz
atlas-chart/src/test/resources/graphengine/data/heatmap_timer_small.json.gz
atlas-chart/src/test/resources/graphengine/data/heatmap_timer.json.gz
atlas-chart/src/test/resources/graphengine/data/heatmap_timer2.json.gz
atlas-chart/src/test/resources/graphengine/data/heatmap_timer3.json.gz

- **Authoritative Scala references to mirror**:
  - Test suites that create graphs: `com.netflix.atlas.chart.DefaultGraphEngineSuite` (extends `PngGraphEngineSuite`).
  - Engine used by tests: `DefaultGraphEngine`.
  - Standalone reference runner: `atlas-chart/src/main/scala/com/netflix/atlas/chart/tools/ChartRenderRunner.scala` (invoked via `runMain`).
  - These define the expected parsing and rendering semantics to reproduce on the Python side.

- **Python approach**:
  - Parameters: Construct using `src_python_gui/atlas_graph_models.py` (Pydantic models/enums) analogous to API query params, but pass them as function arguments (no HTTP request).
  - Data input: Load local JSON/JSON.GZ files from the paths above (V1 and V2 formats).
  - Rendering: Implement a small Python renderer that maps parameters to drawing operations and writes PNG files locally (library choice TBD; e.g., matplotlib/Pillow/cairo).
  - Outputs: PNG (and optionally CSV/TXT/JSON as already modeled by enums), written to a `target/python_manual/` directory.
  - No server process; no Atlas in‑memory database.

- **Makefile (optional convenience)**:
  - Add a `py-chart-runner` target that calls a Python entrypoint with args `--input <json|json.gz> --output <out.png> [--theme light|dark]` mirroring the Scala `ChartRenderRunner` UX.

- **Acceptance Criteria (Python local)**:
  - Given `default_non_uniformly_drawn_spikes.json` and a minimal `GraphRequest`, the Python tool writes a PNG to `target/python_manual/default_non_uniformly_drawn_spikes.png`.
  - Behavior aligns with `DefaultGraphEngine` semantics for core cases used in the selected sample(s).
  - No Atlas server or in‑memory DB is started during the run.
