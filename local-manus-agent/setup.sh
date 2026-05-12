#!/bin/bash
echo "================================================"
echo "Local Manus Agent - Setup (Linux/macOS)"
echo "================================================"
echo

python3 scripts/check_requirements.py
if [ $? -ne 0 ]; then
    echo
    echo "Fix missing requirements first."
    exit 1
fi

echo
python3 scripts/setup.py
