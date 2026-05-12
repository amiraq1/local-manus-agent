#!/bin/bash
echo "Starting Local Manus Agent (Termux)..."
export PLATFORM_MODE=termux
python3 scripts/start_termux.py "$@"
