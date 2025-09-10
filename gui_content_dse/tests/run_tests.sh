#!/usr/bin/env bash
set -euo pipefail

# Simple runner: run all GUI-related tests under this package
python3 -m unittest -v gui_content_dse/tests/*.py

# chmod +x gui_content_dse/tests/run_tests.sh
# gui_content_dse/tests/run_tests.sh

# ow To Run Locally

# bash gui_content_dse/tests/run_tests.sh
# Or: python -m unittest -v gui_content_dse/tests/test_gui.py
# Notes
