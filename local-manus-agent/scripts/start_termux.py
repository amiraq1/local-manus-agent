#!/usr/bin/env python3
"""Start Local Manus Agent on Termux."""
import subprocess
import sys
import os
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
HOST = "127.0.0.1"


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("Local Manus Agent - Termux Start")
    print("=" * 50)

    if dry_run:
        print("[DRY RUN]\n")
        print(f"Would start backend:  uvicorn app.main:app --host {HOST} --port 8000")
        print(f"Would start frontend: npm run dev (cwd: {FRONTEND})")
        print(f"\nURLs:")
        print(f"  Backend:  http://{HOST}:8000")
        print(f"  Frontend: http://{HOST}:3000")
        return

    # Set Termux env
    os.environ["PLATFORM_MODE"] = "termux"

    print(f"\nStarting backend on {HOST}:8000...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", "8000"],
        cwd=str(BACKEND),
    )

    print(f"Starting frontend on {HOST}:3000...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(FRONTEND),
    )

    time.sleep(3)
    print("\n" + "=" * 50)
    print(f"  Backend:  http://{HOST}:8000")
    print(f"  Frontend: http://{HOST}:3000")
    print("=" * 50)
    print("\nPress Ctrl+C to stop.")

    try:
        while True:
            if backend.poll() is not None:
                print("Backend stopped.")
                break
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping...")
        backend.terminate()
        frontend.terminate()
        backend.wait(timeout=5)
        frontend.wait(timeout=5)
        print("Stopped ✓")


if __name__ == "__main__":
    main()
