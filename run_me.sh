#!/bin/bash

# Elite Job Agent - Universal Runner
# This script automatically sets up the environment and launches the application.

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "========================================"
echo "🚀 Elite Job Agent - Terminal Runner"
echo "========================================"

# 1. Detect Python
echo "🔍 Checking for Python..."
if command -v python3 &> /dev/null; then
    PYTHON_EXE="python3"
elif command -v python &> /dev/null; then
    PYTHON_EXE="python"
else
    echo "❌ Python 3 not found! Please install Python from https://python.org"
    exit 1
fi
echo "✅ Found: $($PYTHON_EXE --version)"

# 2. Setup Virtual Environment
echo "🐍 Setting up virtual environment..."
VENV_PATH="$PROJECT_ROOT/.venv_run"
if [ ! -d "$VENV_PATH" ]; then
    echo "✨ Creating new virtual environment in $VENV_PATH..."
    $PYTHON_EXE -m venv "$VENV_PATH"
fi

# Activate venv
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
elif [ -f "$VENV_PATH/Scripts/activate" ]; then
    # Windows/Git Bash fallback
    source "$VENV_PATH/Scripts/activate"
fi

# 3. Install/Update Dependencies
echo "📚 Verifying dependencies..."
pip install --upgrade pip --quiet
pip install --prefer-binary -r requirements.txt --quiet

# 4. Run the Application
echo "🏁 Launching Elite Job Agent..."
echo "----------------------------------------"
python main.py
echo "----------------------------------------"
echo "✅ Application closed."
