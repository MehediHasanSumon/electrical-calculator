#!/usr/bin/env bash
# ================================================================
#  Electrical Calculator - Linux launcher
# ================================================================

set -e

# Change to the directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/venv"

echo "======================================================="
echo "             ELECTRICAL CALCULATOR (LINUX)             "
echo "======================================================="
echo ""

echo "Checking application files..."
if [ ! -f "$SCRIPT_DIR/main.py" ]; then
    echo "Error: main.py was not found." >&2
    exit 1
fi
echo "[OK] main.py found."
echo ""

# Find Python 3
echo "Checking Python..."
SYSTEM_PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    SYSTEM_PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    if python -c "import sys; sys.exit(0 if sys.version_info.major == 3 else 1)" >/dev/null 2>&1; then
        SYSTEM_PYTHON="python"
    fi
fi

if [ -z "$SYSTEM_PYTHON" ]; then
    echo "Error: Python 3 was not found." >&2
    echo "Please install Python 3 (python3) and ensure it is in your PATH." >&2
    exit 1
fi

PYTHON_VERSION="$($SYSTEM_PYTHON --version 2>&1)"
echo "[OK] $PYTHON_VERSION"
echo ""

# Check / Setup Virtual Environment
echo "Checking Virtual Environment..."
if [ ! -f "$VENV_DIR/bin/python" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    rm -rf "$VENV_DIR"
    "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
    echo "[OK] Virtual environment created."
else
    echo "[OK] Virtual environment is ready."
fi
echo ""

# Activate Virtual Environment
echo "Activating Virtual Environment..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"
echo "[OK] Virtual environment activated."
echo ""

# Install Requirements if needed
if [ -f "$SCRIPT_DIR/requirements.txt" ]; then
    if ! python -c "import rich, colorama" >/dev/null 2>&1; then
        echo "Installing Dependencies..."
        python -m pip install -q -r "$SCRIPT_DIR/requirements.txt"
        echo "[OK] Dependencies installed."
    else
        echo "[OK] Dependencies are ready."
    fi
else
    echo "[WARNING] requirements.txt not found. Skipping dependency installation."
fi
echo ""

# Run Application
echo "Starting Application..."
echo ""
echo "======================================================="
echo ""

set +e
python main.py
APP_EXIT_CODE=$?

if [ $APP_EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Application exited with code $APP_EXIT_CODE."
fi

exit $APP_EXIT_CODE
