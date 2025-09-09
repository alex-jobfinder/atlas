# Chart Render Runner

## 1) Human Guide (markdown + ASCII diagrams)

The Chart Render Runner is a tiny Scala entrypoint that renders PNG charts from graph JSON files without relying on test-only, font-gated assertions. It lives at:
- `atlas-chart/src/main/scala/com/netflix/atlas/chart/tools/ChartRenderRunner.scala`

What it does
- Reads a graph JSON (V1 test JSON or V2 `JsonCodec` JSON, `.gz` supported for V2).
- Optionally applies a theme (`light` or `dark`) or renders both.
- Uses `DefaultGraphEngine` to produce PNG files to disk.

Inputs and outputs
- Input: path to JSON (e.g., `atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json`).
- Output: one or two PNGs under `atlas-chart/target/manual/` (default) or a custom output path.

CLI flags
- `--input|-i <path>`: JSON file to render (required)
- `--output|-o <path.png>`: output file path; used as base when `--both`
- `--format v1|v2`: parse as legacy V1 or V2 JsonCodec format (auto-detects V2 for `.json.gz`)
- `--theme light|dark`: apply theme and render a single PNG
- `--both`: render both themes (writes `<out>.png` and `<out>_dark.png`)

Quick usage (sbt wrapper)
- Single theme (dark):
  - `project/sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json --output atlas-chart/target/manual/default_non_uniformly_drawn_spikes.png --theme dark'`
- Both themes:
  - `project/sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json --output atlas-chart/target/manual/default_non_uniformly_drawn_spikes.png --both'`

Makefile helpers
- Render the bundled sample (both themes):
  - `make chart-runner-sample`
- Render a custom JSON (both themes):
  - `make chart-runner RUNNER_IN=path/to/graph.json RUNNER_OUTPREFIX=atlas-chart/target/manual/my_chart`

ASCII flow (single render)
```
       +-------------------+         +-------------------+         +---------------------+
       |  JSON input file  | ----->  |  ChartRenderRunner|  ----->  | DefaultGraphEngine  |
       |  (V1 or V2)       |         |  (parse + theme)  |          |  (PNG generation)   |
       +-------------------+         +-------------------+         +---------+-----------+
                                                                            |
                                                                            v
                                                                    +---------------+
                                                                    |   out.png     |
                                                                    +---------------+
```

ASCII flow (both themes)
```
       +-------------------+
       |  JSON input file  |
       +---------+---------+
                 |
                 v
       +-------------------+        +-------------------------------+
       | ChartRenderRunner | -----> | apply theme(light)  -> out.png|
       |  parse + branch   | -----> | apply theme(dark)   -> out_dark.png
       +-------------------+        +-------------------------------+
```

Notes
- Requires JDK 17 (build config enforces `--release 17`). Use the included sbt wrapper: `project/sbt`.
- Runner bypasses font-gated test assertions, so it produces PNGs on any platform.

---

## 2) Machine Guide (JSON for GPT agents)

```json
{
  "tool": {
    "name": "ChartRenderRunner",
    "module": "atlas-chart",
    "entrypoint": "com.netflix.atlas.chart.tools.ChartRenderRunner",
    "path": "atlas-chart/src/main/scala/com/netflix/atlas/chart/tools/ChartRenderRunner.scala",
    "requires": {
      "java": ">=17",
      "sbt": "use repo wrapper at project/sbt"
    }
  },
  "purpose": "Render PNG charts from Atlas graph JSON (V1 or V2 JsonCodec) without test-only font gating.",
  "inputs": {
    "input_json": {
      "flag": "--input|-i",
      "required": true,
      "desc": "Path to graph JSON (V1: test-style; V2: JsonCodec; .gz supported for V2)"
    },
    "output_png": {
      "flag": "--output|-o",
      "required": false,
      "default": "target/manual/<json-basename>.png",
      "desc": "Output file (used as base when --both)"
    },
    "format": {
      "flag": "--format",
      "enum": ["v1", "v2"],
      "autodetect": "v2 if .json.gz, else v1",
      "desc": "Parser selection"
    },
    "theme": {
      "flag": "--theme",
      "enum": ["light", "dark"],
      "desc": "Single render theme"
    },
    "both": {
      "flag": "--both",
      "desc": "Render both themes; writes <out>.png and <out>_dark.png"
    }
  },
  "outputs": {
    "png_light": "<out>.png",
    "png_dark": "<out>_dark.png (only when --both)"
  },
  "commands": {
    "single_theme": "project/sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input <in.json> --output <out.png> --theme dark'",
    "both_themes": "project/sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input <in.json> --output <out.png> --both'",
    "make_sample": "make chart-runner-sample",
    "make_custom": "make chart-runner RUNNER_IN=<in.json> RUNNER_OUTPREFIX=<prefix>"
  },
  "files": {
    "runner": "atlas-chart/src/main/scala/com/netflix/atlas/chart/tools/ChartRenderRunner.scala",
    "makefile_targets": [
      "chart-runner-sample",
      "chart-runner"
    ],
    "sample_input": "atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json",
    "sample_outputs": [
      "atlas-chart/target/manual/default_non_uniformly_drawn_spikes.png",
      "atlas-chart/target/manual/default_non_uniformly_drawn_spikes_dark.png"
    ]
  },
  "assumptions": [
    "JDK 17 installed and active",
    "Use repo sbt wrapper (no global sbt needed)",
    "Headless AWT is acceptable (JAVA_TOOL_OPTIONS may include -Djava.awt.headless=true)"
  ],
  "failure_modes": [
    {
      "symptom": "Compile error about GLIBC or scala-cli",
      "action": "Ignore scala-cli; use project/sbt"
    },
    {
      "symptom": "Java version < 17",
      "action": "Install OpenJDK 17 and re-run"
    }
  ]
}
```

---

## 3) PRD Next Steps

(tbd)
