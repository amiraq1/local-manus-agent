#!/usr/bin/env python3
"""Setup Local Manus Agent for Termux (Android)."""
import subprocess
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def run(cmd, **kwargs):
    print(f"  → {cmd}")
    return subprocess.run(cmd, shell=True, **kwargs)


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("Local Manus Agent - Termux Setup")
    print("=" * 50)

    if dry_run:
        print("[DRY RUN]\n")

    # 1. System packages
    print("\n[1/4] System packages...")
    cmds = [
        "pkg update -y",
        "pkg install -y python nodejs git clang make openssl libffi",
    ]
    for cmd in cmds:
        if dry_run:
            print(f"  Would run: {cmd}")
        else:
            run(cmd)

    # 2. Python dependencies
    print("\n[2/4] Python backend...")
    if dry_run:
        print(f"  Would install: {BACKEND / 'requirements.txt'}")
    else:
        run(f"pip install -r {BACKEND / 'requirements.txt'}")

    # 3. Frontend
    print("\n[3/4] Frontend...")
    if dry_run:
        print(f"  Would run: npm install in {FRONTEND}")
    else:
        run("npm install", cwd=str(FRONTEND))

    # 4. Workspace
    print("\n[4/4] Workspace...")
    ws = BACKEND / "workspace" / "tasks"
    if not dry_run:
        ws.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {ws}")
    else:
        print(f"  Would create: {ws}")

    print("\n" + "=" * 50)
    print("Termux Setup Complete ✓")
    print("=" * 50)
    print("\nNotes:")
    print("  - Docker Sandbox: NOT available on Termux")
    print("  - Browser Automation: disabled by default")
    print("  - For LLM, use Ollama on a PC:")
    print("    export OLLAMA_BASE_URL=http://<pc-ip>:11434")
    print("\nStart with:")
    print("  python scripts/start_termux.py")


if __name__ == "__main__":
    main()
