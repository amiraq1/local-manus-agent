#!/bin/bash
echo "================================================"
echo "Local Manus Agent - Termux Setup"
echo "================================================"
echo

# Check if running in Termux
if [ -z "$PREFIX" ] || [[ "$PREFIX" != *"com.termux"* ]]; then
    echo "Warning: This script is designed for Termux."
    echo "Use setup.sh for desktop Linux/macOS."
    echo
fi

python3 scripts/setup_termux.py "$@"
