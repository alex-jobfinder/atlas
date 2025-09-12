#!/bin/bash

# Poetry Environment Activation Script
# Source this script to activate the Poetry virtual environment

echo "🚀 Activating Poetry environment for generate-ads-data..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root."
    return 1
fi

# Check if Poetry is installed
if ! command -v poetry >/dev/null 2>&1; then
    echo "❌ Error: Poetry is not installed. Please install Poetry first."
    return 1
fi

# Get Poetry virtual environment path
POETRY_VENV=$(poetry env info --path 2>/dev/null)

if [ -z "$POETRY_VENV" ] || [ ! -d "$POETRY_VENV" ]; then
    echo "❌ Error: Poetry virtual environment not found. Run 'poetry install' first."
    return 1
fi

# Activate the virtual environment
source "$POETRY_VENV/bin/activate"

# Set project-specific environment variables
export DBT_PROFILES_DIR="$(pwd)/dbt_models"
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Add Poetry to PATH
export PATH="$(pwd)/.venv/bin:$PATH"

echo "✅ Poetry virtual environment activated: $(basename "$POETRY_VENV")"
echo "📁 DBT profiles directory: $DBT_PROFILES_DIR"
echo "🐍 Python: $(which python)"
echo "📦 Poetry: $(which poetry)"
echo "🔧 DBT: $(which dbt)"

# Show available commands
echo ""
echo "🚀 Available commands:"
echo "  dbt --version          # Check DBT version"
echo "  dbt debug              # Debug DBT connection"
echo "  dbt run                # Run DBT models"
echo "  dbt test               # Run DBT tests"
echo "  poetry run python      # Run Python with Poetry"
echo "  poetry add <package>   # Add new package"
echo ""
echo "💡 Tip: Use 'deactivate' to exit the virtual environment"
