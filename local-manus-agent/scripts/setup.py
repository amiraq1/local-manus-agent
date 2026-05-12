#!/usr/bin/env python3
"""Setup Local Manus Agent - install all dependencies."""
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
VENV = ROOT / ".venv"


def run(cmd, cwd=None, check=True):
    print(f"  → {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    r = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
    if check and r.returncode != 0:
        print(f"  ✗ Command failed (exit {r.returncode})")
        return False
    return True


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("Local Manus Agent - Setup")
    print("=" * 50)

    if dry_run:
        print("[DRY RUN - no changes will be made]\n")

    # 1. Python venv + backend deps
    print("\n[1/5] Python backend dependencies...")
    if not dry_run:
        if not VENV.exists():
            run([sys.executable, "-m", "venv", str(VENV)])
        pip = str(VENV / ("Scripts" if os.name == "nt" else "bin") / "pip")
        run([pip, "install", "-r", str(BACKEND / "requirements.txt")])
    else:
        print(f"  Would create venv at {VENV}")
        print(f"  Would install {BACKEND / 'requirements.txt'}")

    # 2. Playwright
    print("\n[2/5] Playwright chromium...")
    if not dry_run:
        py = str(VENV / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python"))
        run([py, "-m", "playwright", "install", "chromium"], check=False)
    else:
        print("  Would install playwright chromium")

    # 3. Frontend
    print("\n[3/5] Frontend dependencies...")
    if not dry_run:
        run(["npm", "install"], cwd=str(FRONTEND))
    else:
        print(f"  Would run npm install in {FRONTEND}")

    # 4. Docker sandbox (optional)
    print("\n[4/5] Docker sandbox image (optional)...")
    dockerfile = BACKEND / "sandbox.Dockerfile"
    if dockerfile.exists():
        try:
            r = subprocess.run(["docker", "--version"], capture_output=True)
            if r.returncode == 0:
                if not dry_run:
                    run(["docker", "build", "-f", str(dockerfile), "-t", "local-manus-sandbox:latest", str(BACKEND)], check=False)
                else:
                    print("  Would build sandbox Docker image")
            else:
                print("  ⚠️  Docker not available, skipping sandbox image")
        except FileNotFoundError:
            print("  ⚠️  Docker not installed, skipping sandbox image")
    else:
        print("  ⚠️  sandbox.Dockerfile not found, skipping")

    # 5. Create workspace
    print("\n[5/5] Workspace directories...")
    workspace = BACKEND / "workspace"
    workspace.mkdir(exist_ok=True)
    (workspace / "tasks").mkdir(exist_ok=True)
    if not dry_run:
        print(f"  ✓ {workspace}")
    else:
        print(f"  Would create {workspace}")

    print("\n" + "=" * 50)
    print("Setup complete ✓")
    print("=" * 50)
    print("\nNext steps:")
    print("  1. Start Ollama:  ollama serve")
    print("  2. Pull model:    ollama pull qwen2.5-coder:7b")
    print("  3. Run:           python scripts/start.py")


if __name__ == "__main__":
    main()
