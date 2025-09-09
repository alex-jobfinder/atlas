# Context

## the makefile commands run related: atlas-chart/src/main/scala/com/netflix/atlas/chart/tools/ChartRenderRunner.scala to use existing data in atlas-chart/src/test/resources/graphengine/data/ and render to png. We want to replicate this functionality in python.

"""
# Defaults for chart-runner
RUNNER_IN ?= atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json
RUNNER_OUTPREFIX ?= atlas-chart/target/manual/default_non_uniformly_drawn_spikes

.PHONY: chart-runner-sample
chart-runner-sample: ## Render bundled sample to PNG (light and dark)
	@echo "🚀 Rendering sample (light + dark)"
	@project/sbt 'project atlas-chart' \
	  'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input $(RUNNER_IN) --output $(RUNNER_OUTPREFIX).png --both'

.PHONY: chart-runner
chart-runner: ## Render PNG(s) from JSON: RUNNER_IN=<json> RUNNER_OUTPREFIX=<out prefix>
	@test -n "$(RUNNER_IN)" || { echo "Usage: make chart-runner RUNNER_IN=path/to.json [RUNNER_OUTPREFIX=out/prefix]"; exit 2; }
	@echo "🚀 Rendering $(RUNNER_IN) to $(RUNNER_OUTPREFIX).png (light + dark)"
	@project/sbt 'project atlas-chart' \
	  'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input $(RUNNER_IN) --output $(RUNNER_OUTPREFIX).png --both'

"""

## Task
# In atlas-chart, there is atlas-chart/src/test/scala/com/netflix/atlas/chart/PngGraphEngineSuite.scala that can generate Python equivalent of the EngineDataGenerator helpers (the methods in your Scala test suite like constant, wave, interval, etc.) so you can generate synthetic time series data for charts. The core chart model classes (Palette, PlotBound, PlotDef, DataDef with LineDef/HSpanDef/VSpanDef/MessageDef, GraphDef, and HeatmapDef) into Python so they can integrate with your existing EngineDataGenerator.

# The new src_python_gui/EngineDataGenerator.py will be used to generate the synthetic time series data for charts. Its created but not tested. The AtlasGraphModels.py is used to construct the parameters analogous to API; pass those as function args and read data from local file to render graphs.

# reference_path: atlas-chart/src/test/scala/com/netflix/atlas/chart/PngGraphEngineSuite.scala
# python_path: src_python_gui/EngineDataGenerator.py
# atlas_graph_models_path: src_python_gui/atlas_graph_models.py

## Deliverables
"""
## Deliverables
- A python script that can generate a PNG chart from a local JSON file using the EngineDataGenerator and AtlasGraphModels.py.
- A test that can load the JSON file, generate the synthetic time series data, and render a PNG chart.
- A Makefile target that can run the script and generate the PNG chart.
- A README.md file that explains how to use the script and the Makefile target.
- A pytest test that can load the JSON file, generate the synthetic time series data, and render a PNG chart.
"""
