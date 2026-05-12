#!/usr/bin/env sh
echo "Starting Local Manus Agent (Termux)..."

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
else
    echo "Error: Python is not installed. Run: pkg install python"
    exit 1
fi

export PLATFORM_MODE=termux
exec "$PYTHON_BIN" "$SCRIPT_DIR/scripts/start_termux.py" "$@"
