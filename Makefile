# Map stdin to /dev/null to avoid interactive prompts if there is some failure related to the
# build script.
ifeq (${TRAVIS_SCALA_VERSION},)
	SBT := cat /dev/null | project/sbt
else
	SBT := cat /dev/null | project/sbt ++${TRAVIS_SCALA_VERSION}
endif

WIKI_PRG        := atlas-wiki/runMain com.netflix.atlas.wiki.Main
WIKI_INPUT_DIR  := $(shell pwd)/atlas-wiki/src/main/resources
WIKI_OUTPUT_DIR := $(shell pwd)/target/atlas.wiki

LAUNCHER_JAR_URL := https://repo1.maven.org/maven2/com/netflix/iep/iep-launcher/5.1.1/iep-launcher-5.1.1.jar

.PHONY: build snapshot release clean format update-wiki publish-wiki

build:
	$(SBT) clean test checkLicenseHeaders scalafmtCheckAll

snapshot:
	# Travis uses a depth when fetching git data so the tags needed for versioning may not
	# be available unless we explicitly fetch them
	git fetch --unshallow --tags
	$(SBT) storeBintrayCredentials
	$(SBT) clean test checkLicenseHeaders publish

release:
	# Travis uses a depth when fetching git data so the tags needed for versioning may not
	# be available unless we explicitly fetch them
	git fetch --unshallow --tags

	# Storing the bintray credentials needs to be done as a separate command so they will
	# be available early enough for the publish task.
	#
	# The storeBintrayCredentials still needs to be on the subsequent command or we get:
	# [error] (iep-service/*:bintrayEnsureCredentials) java.util.NoSuchElementException: None.get
	$(SBT) storeBintrayCredentials
	$(SBT) clean test checkLicenseHeaders storeBintrayCredentials publish bintrayRelease

clean:
	$(SBT) clean

format:
	$(SBT) formatLicenseHeaders scalafmtAll

$(WIKI_OUTPUT_DIR):
	mkdir -p target
	git clone git@github.com:Netflix/atlas.wiki.git $(WIKI_OUTPUT_DIR)

update-wiki: $(WIKI_OUTPUT_DIR)
	cd $(WIKI_OUTPUT_DIR) && git rm -rf *
	$(SBT) "$(WIKI_PRG) $(WIKI_INPUT_DIR) $(WIKI_OUTPUT_DIR)"

publish-wiki: update-wiki
	cd $(WIKI_OUTPUT_DIR) && git add * && git status
	cd $(WIKI_OUTPUT_DIR) && git commit -a -m "update wiki"
	cd $(WIKI_OUTPUT_DIR) && git push origin master

one-jar:
	mkdir -p target
	curl -L $(LAUNCHER_JAR_URL) -o target/iep-launcher.jar
	java -classpath target/iep-launcher.jar com.netflix.iep.launcher.JarBuilder \
		target/standalone.jar com.netflix.atlas.standalone.Main \
		`$(SBT) "export atlas-standalone/runtime:fullClasspath" | tail -n1 | sed 's/:/ /g'`



# -----------------------------
# Python (root project) targets
# -----------------------------

# Usage:
#   make help          # show documented targets
#   make install       # create venv via uv and install hooks
#   make check         # lint, type-check, tests
#   make test          # run tests only
#   make py-install    # alias for install
#   make py-check      # alias for check
#   make py-test       # alias for test

.PHONY: help
help: ## Show available targets and descriptions
	@awk 'BEGIN {FS=":.*## "} /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: install
install: ## Install the virtual environment and install the pre-commit hooks
	@echo "🚀 Creating virtual environment using uv"
	@uv sync
	@uv run pre-commit install

.PHONY: check
check: ## Run code quality tools
	@echo "🚀 Checking lock file consistency with 'pyproject.toml'"
	@uv lock --locked
	@echo "🚀 Linting code: Running pre-commit"
	@uv run pre-commit run -a
	@echo "🚀 Static type checking: Running ty"
	@uv run ty check src scripts tests
	@echo "🚀 Running tests: pytest must pass"
	@uv run python -m pytest --doctest-modules

.PHONY: test
test: ## Test the code with pytest
	@echo "🚀 Testing code: Running pytest"
	@uv run python -m pytest --doctest-modules

# Aliases with a clear namespace
.PHONY: py-install py-check py-test
py-install: ## Alias for install (Python)
	@$(MAKE) --no-print-directory install
py-check: ## Alias for check (Python)
	@$(MAKE) --no-print-directory check
py-test: ## Alias for test (Python)
	@$(MAKE) --no-print-directory test

################################
# Scala chart runner (atlas-chart)
################################

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


# ----------------------
# Python chart utilities
# ----------------------

# Defaults (override on command line):
#   make py-chart EXPR='name,server.requestCount,:eq,:sum' OUT=chart.png WINDOW=e-6h
BASE_URL ?= http://localhost:7101
EXPR ?= name,server.requestCount,:eq,:sum
WINDOW ?= e-1h
OUT ?= chart.png
STEP ?=
END ?=
NO_LEGEND ?= 1

LOG_DIR := target/logs
PID_DIR := target/pids

# correct way to run the jar (foreground)
py-run-jar:
	java -jar atlas-standalone-1.7.8.jar

## steps 1-3 work and verified with py-verify-jar
# # Start/stop helpers (background with logs + pid files)
# .PHONY: py-start-atlas py-stop-atlas py-wait-atlas
py-start-atlas: ## Start Atlas standalone in background
	@mkdir -p target/logs target/pids
	@echo "🚀 Starting Atlas in background"
	@nohup java -jar atlas-standalone-1.7.8.jar > target/logs/atlas.log 2>&1 & echo $$! > target/pids/atlas.pid

py-stop-atlas: ## Stop Atlas standalone
	-@if [ -f target/pids/atlas.pid ]; then kill `cat target/pids/atlas.pid` 2>/dev/null || true; rm -f target/pids/atlas.pid; fi
	-@pkill -f 'atlas-standalone-1.7.8.jar' 2>/dev/null || true

py-wait-atlas: ## Wait until Atlas is responding
	@echo "⏳ Waiting for Atlas on http://localhost:7101"
	@for i in $$(seq 1 30); do \
	  if curl -sf http://localhost:7101/api/v1/tags >/dev/null; then echo "✅ Atlas ready"; exit 0; fi; \
	  sleep 1; \
	done; echo "❌ Atlas not responding"; exit 1

# verified
py-verify-jar:
	curl http://localhost:7101/api/v1/tags

# ## output make py-verify-jar
# 0	"name"
# 1	"nf.app"
# 2	"nf.asg"
# 3	"nf.cluster"
# 4	"nf.node"
# 5	"percentile"
# 6	"statistic"
# 7	"type"
# 8	"type2"

.PHONY: py-start-spectatord py-stop-spectatord py-wait-spectatord py-spectatord-status
# Auto-start: prefer local binary; fallback to Docker if available
.PHONY: py-start-spectatord-auto
py-start-spectatord-auto: ## Start SpectatorD (local if available, else Docker)
	@command -v spectatord >/dev/null && { $(MAKE) --no-print-directory py-start-spectatord; exit 0; } || true
	@command -v docker >/dev/null || { echo "❌ spectatord not found and docker not available"; exit 1; }
	@$(MAKE) --no-print-directory py-start-spectatord-docker

py-start-spectatord: ## Start SpectatorD (publishing to Atlas)
	@mkdir -p $(LOG_DIR) $(PID_DIR)
	@command -v spectatord >/dev/null || { echo "❌ spectatord not found in PATH"; exit 1; }
	@if pgrep -x spectatord >/dev/null; then echo "SpectatorD already running"; \
	else echo "🚀 Starting SpectatorD" && \
	  (nohup spectatord --uri $(BASE_URL)/api/v1/publish --verbose >$(LOG_DIR)/spectatord.log 2>&1 & echo $$! > $(PID_DIR)/spectatord.pid); fi

py-stop-spectatord: ## Stop SpectatorD
	-@if [ -f $(PID_DIR)/spectatord.pid ]; then kill `cat $(PID_DIR)/spectatord.pid` 2>/dev/null || true; rm -f $(PID_DIR)/spectatord.pid; fi
	-@pkill -x spectatord 2>/dev/null || true

py-wait-spectatord: ## Wait until SpectatorD admin is up
	@echo "⏳ Waiting for SpectatorD admin on http://localhost:1234/"
	@for i in $$(seq 1 20); do \
	  if curl -sf http://localhost:1234/ >/dev/null; then echo "✅ SpectatorD ready"; exit 0; fi; \
	  sleep 1; \
	done; echo "❌ SpectatorD admin not responding on 1234"; exit 1

py-spectatord-status: ## Dump SpectatorD /metrics summary
	@curl -sf http://localhost:1234/metrics | head -n 50 || true

.PHONY: py-start-spectatord-docker py-stop-spectatord-docker
py-start-spectatord-docker: ## Start SpectatorD in Docker (publishing to Atlas)
	@echo "🚀 Starting SpectatorD (Docker)"
	@docker rm -f spectatord >/dev/null 2>&1 || true
	@docker run -d --name spectatord \
	  --add-host host.docker.internal:host-gateway \
	  -p 1234:1234/udp -p 1234:1234 \
	  ghcr.io/netflix-skunkworks/spectatord:latest \
	  --uri http://host.docker.internal:7101/api/v1/publish --verbose >/dev/null

py-stop-spectatord-docker: ## Stop SpectatorD (Docker)
	-@docker rm -f spectatord >/dev/null 2>&1 || true

.PHONY: py-wait-sd-metric
py-wait-sd-metric: ## Wait until SpectatorD /metrics contains NAME=...
	@test -n "$(NAME)" || { echo "Usage: make py-wait-sd-metric NAME=metricName"; exit 2; }
	@echo "⏳ Waiting for SpectatorD to expose $(NAME)"
	@for i in $$(seq 1 20); do \
	  curl -sf http://localhost:1234/metrics | grep -q "$(NAME)" && { echo "✅ SpectatorD has $(NAME)"; exit 0; }; \
	  sleep 1; \
	done; echo "❌ $(NAME) not visible in SpectatorD /metrics"; exit 1

.PHONY: py-start-flask py-stop-flask py-wait-flask
py-start-flask: ## Start Flask app (emits metrics)
	@mkdir -p $(LOG_DIR) $(PID_DIR)
	@echo "🚀 Starting Flask app"
	@(nohup env SPECTATOR_OUTPUT_LOCATION=udp://127.0.0.1:1234 flask --app app run >$(LOG_DIR)/flask.log 2>&1 & echo $$! > $(PID_DIR)/flask.pid)

py-stop-flask: ## Stop Flask app
	-@if [ -f $(PID_DIR)/flask.pid ]; then kill `cat $(PID_DIR)/flask.pid` 2>/dev/null || true; rm -f $(PID_DIR)/flask.pid; fi
	-@pkill -f 'flask --app app run' 2>/dev/null || true

py-wait-flask: ## Wait until Flask responds
	@echo "⏳ Waiting for Flask on http://127.0.0.1:5000/"
	@for i in $$(seq 1 20); do \
	  if curl -sf http://127.0.0.1:5000/ >/dev/null; then echo "✅ Flask ready"; exit 0; fi; \
	  sleep 1; \
	done; echo "❌ Flask not responding on 5000"; exit 1

.PHONY: py-start-curl py-seed-through-spectatord
py-start-curl: ## Generate one request to app (produces metrics)
	curl -s 'http://127.0.0.1:5000/api/v1/play?country=US&title=Demo' || true



# Optional: seed SpectatorD directly (bypass app) to validate pipeline
py-seed-through-spectatord:
	@command -v nc >/dev/null || { echo "❌ 'nc' (netcat) not found"; exit 1; }
	@echo "c:server.requestCount,path=v1_play,country=US,title=Demo,status=200:1" | nc -u -w1 127.0.0.1 1234 || true

.PHONY: py-emit-once py-spectator-unit py-spectator-e2e
py-emit-once: ## Emit one counter via spectator-py to SpectatorD (UDP)
	@echo "🚀 Emitting one server.requestCount via spectator-py"
	@SPECTATOR_OUTPUT_LOCATION=udp://127.0.0.1:1234 \
	uv run python - <<-'PY'
	from spectator import Registry, Config

	registry = Registry(Config())  # default UDP to 127.0.0.1:1234
	request_count_id = registry.new_id("server.requestCount", {"path": "v1_play", "country": "US", "title": "Demo", "status": "200"})
	registry.counter_with_id(request_count_id).increment()
	print("emitted server.requestCount=1")
	PY

py-spectator-unit: ## Unit test spectator-py (memory writer)
	@uv run python - <<-'PY'
	from spectator import Registry, Config

	r = Registry(Config("memory"))
	c = r.counter("server.requestCount", {"status": "200"})
	c.increment()
	print("memory last_line:", r.writer().last_line())
	assert r.writer().last_line().startswith("c:server.requestCount"), "No counter line captured"
	print("✅ spectator memory writer OK")
	PY


py-spectator-e2e: ## Start Atlas+SpectatorD, emit once with spectator, then chart
	@$(MAKE) --no-print-directory py-start-atlas
	@$(MAKE) --no-print-directory py-wait-atlas
	@$(MAKE) --no-print-directory py-start-spectatord-auto
	@$(MAKE) --no-print-directory py-wait-spectatord
	@$(MAKE) --no-print-directory py-emit-once
	@$(MAKE) --no-print-directory py-wait-metric NAME=server.requestCount || true
	@echo "⏳ Give SpectatorD ~5s to publish"; sleep 6
	@$(MAKE) --no-print-directory py-chart-app

# py-verify-chart: py-verify-jar py-chart

.PHONY: live-data py-stack-up py-stack-down py-chart-demo py-chart-app py-wait-metric
live-data: ## Optional: See live data with SpectatorD agent, Flask app, and curl
	@echo "🚀 Starting SpectatorD agent"; $(MAKE) --no-print-directory py-start-spectatord
	@echo "🚀 Starting Flask app to emit metrics"; $(MAKE) --no-print-directory py-start-flask
	@sleep 2
	@echo "🚀 Hitting Flask app to generate data"; $(MAKE) --no-print-directory py-start-curl

py-stack-up: ## Start Atlas + SpectatorD + Flask, wait, then seed and chart
	@$(MAKE) --no-print-directory py-start-atlas
	@$(MAKE) --no-print-directory py-wait-atlas
	@$(MAKE) --no-print-directory py-start-spectatord
	@$(MAKE) --no-print-directory py-wait-spectatord
	@$(MAKE) --no-print-directory py-start-flask
	@$(MAKE) --no-print-directory py-wait-flask
	@for i in $$(seq 1 5); do $(MAKE) --no-print-directory py-start-curl; sleep 1; done
	@echo "⏳ Give SpectatorD ~5s to publish"; sleep 6
	@$(MAKE) --no-print-directory py-chart-app

py-stack-down: ## Stop Flask, SpectatorD, Atlas
	@$(MAKE) --no-print-directory py-stop-flask
	@$(MAKE) --no-print-directory py-stop-spectatord
	@$(MAKE) --no-print-directory py-stop-atlas

py-chart-demo: ## Chart a built-in Atlas metric (sps)
	@$(MAKE) --no-print-directory py-chart EXPR='name,sps,:eq,:sum' WINDOW=e-10m OUT=demo-sps.png

py-chart-app: ## Chart the Flask app's requestCount metric
	@$(MAKE) --no-print-directory py-chart EXPR='name,server.requestCount,:eq,:sum' WINDOW=e-10m OUT=app-requests.png

py-wait-metric: ## Wait until a metric name is visible (NAME=foo)
	@test -n "$(NAME)" || { echo "Usage: make py-wait-metric NAME=metricName"; exit 2; }
	@for i in $$(seq 1 20); do \
	  curl -sf $(BASE_URL)/api/v1/tags/name | grep -q '"'"$(NAME)"'"' && { echo "✅ Found $(NAME)"; exit 0; }; \
	  sleep 1; \
	done; echo "❌ Did not see $(NAME) in tags/name"; exit 1


.PHONY: py-chart
py-chart: ## Fetch a chart PNG from Atlas Graph API (override EXPR, OUT, WINDOW)
	@echo "🚀 Fetching chart from $(BASE_URL) -> $(OUT)"
	@args="--base-url $(BASE_URL) --expr $(EXPR) --window $(WINDOW) --out $(OUT)"; \
	 if [ -n "$(STEP)" ]; then args="$$args --step $(STEP)"; fi; \
	 if [ -n "$(END)" ]; then args="$$args --end $(END)"; fi; \
	 case "$(NO_LEGEND)" in 1|true|yes|on) args="$$args --no-legend";; esac; \
	 echo uv run python -m src_python_gui.cli $$args; \
	 uv run python -m src_python_gui.cli $$args


# ---------------------------------------------
# Python: render PNG directly from local JSON
# ---------------------------------------------
.PHONY: py-chart-from-json
PY_JSON_IN ?= atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json
PY_JSON_OUT ?= atlas-chart/target/manual/default_non_uniformly_drawn_spikes_py.png
THEME ?= light
OVERLAY ?= false
WIDTH ?= 700
HEIGHT ?= 200
STYLE ?= line
AXIS_GROUPS ?=
YLABEL_LEFT ?=
YLABEL_RIGHT ?=

py-chart-from-json: ## Render a PNG from a local atlas-chart JSON (no server)
	@echo "🚀 Rendering local JSON $(PY_JSON_IN) -> $(PY_JSON_OUT) (theme=$(THEME), overlay=$(OVERLAY))"
	@args="-i $(PY_JSON_IN) -o $(PY_JSON_OUT) --theme $(THEME) --width $(WIDTH) --height $(HEIGHT) --style $(STYLE)"; \
	 case "$(OVERLAY)" in 1|true|yes|on) args="$$args --overlay-wave";; esac; \
	 if [ -n "$(AXIS_GROUPS)" ]; then args="$$args --axis-groups $(AXIS_GROUPS)"; fi; \
	 if [ -n "$(YLABEL_LEFT)" ]; then args="$$args --ylabel-left $(YLABEL_LEFT)"; fi; \
	 if [ -n "$(YLABEL_RIGHT)" ]; then args="$$args --ylabel-right $(YLABEL_RIGHT)"; fi; \
	 echo uv run python -m src_python_gui.chart_from_json $$args; \
	 uv run python -m src_python_gui.chart_from_json $$args
