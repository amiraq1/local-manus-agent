#!/usr/bin/env python3
"""Development mode - check, start, and watch with graceful shutdown."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent


def main():
    print("=" * 50)
    print("Local Manus Agent - Dev Mode")
    print("=" * 50)

    # 1. Check requirements
    print("\n[1] Checking requirements...")
    r = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_requirements.py")])
    if r.returncode != 0:
        print("\nFix missing requirements before continuing.")
        sys.exit(1)

    # 2. Start services
    print("\n[2] Starting services...")
    try:
        subprocess.run([sys.executable, str(ROOT / "scripts" / "start.py")])
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
