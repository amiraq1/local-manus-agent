#!/usr/bin/env python3
"""Setup Local Manus Agent for Termux (Android)."""
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
TERMUX_REQUIREMENTS = BACKEND / "requirements-termux.txt"


def format_cmd(cmd):
    if isinstance(cmd, (list, tuple)):
        return " ".join(shlex.quote(str(part)) for part in cmd)
    return str(cmd)


def run(cmd, cwd=None, check=True):
    print(f"  → {format_cmd(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str))
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result


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
        ["pkg", "update", "-y"],
        ["pkg", "install", "-y", "python", "nodejs", "git", "clang", "make", "openssl", "libffi"],
    ]
    try:
        for cmd in cmds:
            if dry_run:
                print(f"  Would run: {format_cmd(cmd)}")
            else:
                run(cmd)

        # 2. Python dependencies
        print("\n[2/4] Python backend...")
        if dry_run:
            print(f"  Would install: {TERMUX_REQUIREMENTS}")
            print("  Note: Playwright is skipped on Termux because browser automation is disabled there.")
        else:
            print("  Skipping Playwright on Termux because browser automation is disabled.")
            run([sys.executable, "-m", "pip", "install", "-r", str(TERMUX_REQUIREMENTS)])

        # 3. Frontend
        print("\n[3/4] Frontend...")
        if dry_run:
            print(f"  Would run: npm install in {FRONTEND}")
            print("  Would patch Next.js SWC loader to use wasm on Android/Termux")
        else:
            run(["npm", "install"], cwd=str(FRONTEND))
            run([sys.executable, str(ROOT / "scripts" / "patch_next_termux.py")], cwd=str(ROOT))

        # 4. Workspace
        print("\n[4/4] Workspace...")
        ws = BACKEND / "workspace" / "tasks"
        if not dry_run:
            ws.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {ws}")
        else:
            print(f"  Would create: {ws}")
    except subprocess.CalledProcessError as exc:
        print(f"\nSetup failed while running: {format_cmd(exc.cmd)}")
        print(f"Exit code: {exc.returncode}")
        return 1

    print("\n" + "=" * 50)
    print("Termux Setup Complete ✓")
    print("=" * 50)
    print("\nNotes:")
    print("  - Docker Sandbox: NOT available on Termux")
    print("  - Browser Automation: disabled by default")
    print("  - For LLM, use Ollama on a PC:")
    print("    export OLLAMA_BASE_URL=http://<pc-ip>:11434")
    print("\nStart with:")
    print("  ./start-termux.sh")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
