VENV := .venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: venv install deps setup init-db run-config-seed seed-5x5-no-init clean test dbt-seed dbt-run dbt-run-staging dbt-run-marts dbt-test dbt-test-model dbt-pipeline dbt-fresh clean-dbt dbt-debug dbt-list dbt-show query-db docs-html docs-serve docs-html-strict docs-serve-fresh

venv:
	python3 -m venv $(VENV)

install: venv
	$(PIP) install --upgrade pip
	$(PIP) install "sqlalchemy>=2" "click>=8" "pydantic[email]>=2" "faker>=19" "pytest>=7" "colorlog>=6" "pyyaml>=6" "rich>=13"

deps: install

init-db: deps
	$(PY) cli.py db init

setup: init-db
	@echo "Environment ready."

# Initialize DB, load config.yml, then seed 5x5 with performance
run-config-seed: init-db
	$(PY) cli.py create-from-config --path "config.yml" --generate-performance
	@for i in $$(seq 1 5); do \
	  ADV_ID=$$($(PY) -c 'import json,subprocess; p=subprocess.run(["$(PY)","cli.py","campaign","create-advertiser","--auto"], capture_output=True, text=True, check=True); print(json.loads(p.stdout)["advertiser_id"])'); \
	  echo "Created Advertiser $$i => ID=$$ADV_ID"; \
	  for j in $$(seq 1 5); do \
	    $(PY) cli.py campaign create --advertiser-id $$ADV_ID --auto --generate-performance; \
	  done; \
	  echo "---"; \
	done

# Seed 5x5 without resetting DB (no init) - WITH performance generation
seed-5x5-no-init: deps
	@for i in $$(seq 1 5); do \
	  ADV_ID=$$($(PY) -c 'import json,subprocess; p=subprocess.run(["$(PY)","cli.py","campaign","create-advertiser","--auto"], capture_output=True, text=True, check=True); print(json.loads(p.stdout)["advertiser_id"])'); \
	  echo "Created Advertiser $$i => ID=$$ADV_ID"; \
	  for j in $$(seq 1 5); do \
	    $(PY) cli.py campaign create --advertiser-id $$ADV_ID --auto --generate-performance; \
	  done; \
	  echo "---"; \
	done

# NEW: 5x5 seeding with batch performance generation (all-in-one command)
seed-5x5-batch: deps
	$(PY) cli.py create-from-config --seed-5x5 --generate-performance --performance-type both

# NEW: 5x5 seeding with normal performance only (batch inserts)
seed-5x5-normal: deps
	$(PY) cli.py create-from-config --seed-5x5 --generate-performance --performance-type normal

# NEW: 5x5 seeding with extended performance only (batch inserts)
seed-5x5-extended: deps
	$(PY) cli.py create-from-config --seed-5x5 --generate-performance --performance-type extended

# NEW: 5x5 seeding with custom seed for reproducible data
seed-5x5-reproducible: deps
	$(PY) cli.py create-from-config --seed-5x5 --generate-performance --performance-type both --seed 42

# NEW: Fresh setup with config + 5x5 + batch performance
run-config-seed-5x5: init-db
	$(PY) cli.py create-from-config --path "config.yml" --generate-performance
	$(PY) cli.py create-from-config --seed-5x5 --generate-performance --performance-type both

test: deps
	$(PY) -m pytest -q

clean:
	rm -f ads.db ads_p0.db ads_p0.db-shm ads_p0.db-wal
	rm -rf __pycache__ .pytest_cache $(VENV)

# Run all tests                                                                                                                                                                                                                   ─╯
# poetry run pytest

# # Run specific test files
# poetry run pytest tests/test_performance_metrics.py

# # Generate data
# poetry run python cli.py init-db
# poetry run ./run_all.sh

# # Format and lint code
# poetry run black .
# poetry run ruff check .

# =============================================================================
# DBT Commands
# =============================================================================

# DBT Seed - Load CSV data into database
dbt-seed:
	@echo "🌱 Running DBT Seed..."
	cd dbt_ads_project && dbt seed --select campaign_performance

# DBT Run - Execute all models
dbt-run:
	@echo "🚀 Running DBT Models..."
	cd dbt_ads_project && dbt run

# DBT Run Staging Only
dbt-run-staging:
	@echo "📊 Running DBT Staging Models..."
	cd dbt_ads_project && dbt run --select staging

# DBT Run Marts Only
dbt-run-marts:
	@echo "🏪 Running DBT Mart Models..."
	cd dbt_ads_project && dbt run --select marts

# DBT Test - Run all tests
dbt-test:
	@echo "🧪 Running DBT Tests..."
	cd dbt_ads_project && dbt test

# DBT Test Specific Model
dbt-test-model:
	@echo "🧪 Testing Specific Model..."
	cd dbt_ads_project && dbt test --select stg_hourly_campaign_performance

# DBT Full Pipeline - Seed, Run, Test
dbt-pipeline: dbt-seed dbt-run dbt-test
	@echo "✅ DBT Pipeline Complete!"

# DBT Fresh Start - Clean and rebuild everything
dbt-fresh: clean-dbt
	@echo "🔄 Fresh DBT Start..."
	cd dbt_ads_project && dbt seed --select campaign_performance
	cd dbt_ads_project && dbt run
	cd dbt_ads_project && dbt test

# Clean DBT artifacts
clean-dbt:
	@echo "🧹 Cleaning DBT artifacts..."
	cd dbt_ads_project && rm -rf target/ logs/ dbt.duckdb*

# DBT Debug - Show project info
dbt-debug:
	@echo "🔍 DBT Debug Info..."
	cd dbt_ads_project && dbt debug

# DBT List - Show available models
dbt-list:
	@echo "📋 Available DBT Models:"
	cd dbt_ads_project && dbt list

# DBT Show - Show model details
dbt-show:
	@echo "📊 DBT Model Details:"
	cd dbt_ads_project && dbt show --select stg_hourly_campaign_performance

# Query DuckDB - Run analysis script
query-db:
	@echo "🔍 Running DuckDB Analysis..."
	cd dbt_ads_project && python query_duckdb.py

# =============================================================================
# Documentation (Sphinx)
# =============================================================================

docs-html:
	@echo "📚 Building Sphinx HTML docs..."
	poetry run make -C docs html
	@echo "✅ Docs built: docs/_build/html/index.html"

docs-serve:
	@echo "🌐 Starting Sphinx live server on http://127.0.0.1:8000 ..."
	poetry run make -C docs serve

docs-html-strict:
	@echo "📚 Building Sphinx HTML docs with warnings as errors..."
	poetry run make -C docs html-strict

docs-serve-fresh:
	@echo "🔪 Freeing port 8000 (if in use) and launching live docs..."
	@# Try fuser first, fall back to lsof if available
	-@if command -v fuser >/dev/null 2>&1; then \
	  fuser -k 8000/tcp || true; \
	elif command -v lsof >/dev/null 2>&1; then \
	  PIDS=$$(lsof -ti tcp:8000); \
	  if [ -n "$$PIDS" ]; then kill -9 $$PIDS || true; fi; \
	else \
	  echo "ℹ️  Neither fuser nor lsof found; continuing without freeing port."; \
	fi
	@echo "🌐 Opening http://127.0.0.1:8000 ..."
	poetry run make -C docs serve AUTOBUILD="sphinx-autobuild --open-browser"
