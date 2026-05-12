#!/usr/bin/env sh
echo "================================================"
echo "Local Manus Agent - Termux Setup"
echo "================================================"
echo

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT_DIR=$SCRIPT_DIR
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
REQUIREMENTS_FILE="$BACKEND_DIR/requirements-termux.txt"
PATCHER_SCRIPT="$ROOT_DIR/scripts/patch_next_termux.py"
DRY_RUN=0

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
else
    echo "Error: Python is not installed. Run: pkg install python"
    exit 1
fi

# Check if running in Termux
case "${PREFIX:-}" in
    *com.termux*)
        ;;
    *)
    echo "Warning: This script is designed for Termux."
    echo "Use setup.sh for desktop Linux/macOS."
    echo
        ;;
esac

if [ "${1:-}" = "--dry-run" ]; then
    DRY_RUN=1
    echo "[DRY RUN]"
    echo
fi

run_cmd() {
    echo "  → $*"
    if [ "$DRY_RUN" -eq 1 ]; then
        return 0
    fi
    "$@"
}

run_in_dir() {
    dir=$1
    shift
    echo "  → $*"
    if [ "$DRY_RUN" -eq 1 ]; then
        return 0
    fi
    (
        cd "$dir" || exit 1
        "$@"
    )
}

echo "[1/4] System packages..."
run_cmd pkg update -y || exit 1
run_cmd pkg install -y python nodejs git clang make openssl libffi || exit 1

echo
echo "[2/4] Python backend..."
echo "  Skipping Playwright on Termux because browser automation is disabled."
run_cmd "$PYTHON_BIN" -m pip install -r "$REQUIREMENTS_FILE" || exit 1

echo
echo "[3/4] Frontend..."
run_in_dir "$FRONTEND_DIR" npm install || exit 1
run_cmd "$PYTHON_BIN" "$PATCHER_SCRIPT" || exit 1

echo
echo "[4/4] Workspace..."
if [ "$DRY_RUN" -eq 1 ]; then
    echo "  Would create: $BACKEND_DIR/workspace/tasks"
else
    mkdir -p "$BACKEND_DIR/workspace/tasks" || exit 1
    echo "  ✓ $BACKEND_DIR/workspace/tasks"
fi

echo
echo "=================================================="
echo "Termux Setup Complete ✓"
echo "=================================================="
echo
echo "Notes:"
echo "  - Docker Sandbox: NOT available on Termux"
echo "  - Browser Automation: disabled by default"
echo "  - For LLM, use Ollama on a PC:"
echo "    export OLLAMA_BASE_URL=http://<pc-ip>:11434"
echo
echo "Start with:"
echo "  ./start-termux.sh"
