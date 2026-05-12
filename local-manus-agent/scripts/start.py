#!/usr/bin/env python3
"""Start Local Manus Agent - backend + frontend."""
import subprocess
import sys
import os
import time
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
PID_DIR = ROOT / ".local-manus"
PID_DIR.mkdir(exist_ok=True)


def get_python():
    """Get the venv python or system python."""
    venv_py = ROOT / ".venv" / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def start_backend():
    """Start the backend server."""
    py = get_python()
    proc = subprocess.Popen(
        [py, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=str(BACKEND),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    (PID_DIR / "backend.pid").write_text(str(proc.pid))
    return proc


def start_frontend():
    """Start the frontend dev server."""
    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(FRONTEND),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=(os.name == "nt"),
    )
    (PID_DIR / "frontend.pid").write_text(str(proc.pid))
    return proc


def check_ollama():
    """Check if Ollama is running."""
    try:
        import urllib.request
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return r.status == 200
    except Exception:
        return False


def wait_for_backend(timeout=15):
    """Wait for backend to be ready."""
    for _ in range(timeout * 2):
        try:
            import urllib.request
            r = urllib.request.urlopen("http://localhost:8000/api/health", timeout=2)
            if r.status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("Local Manus Agent - Start")
    print("=" * 50)

    if dry_run:
        print("[DRY RUN]\n")
        print("Would start:")
        print(f"  Backend:  uvicorn app.main:app --port 8000 (cwd: {BACKEND})")
        print(f"  Frontend: npm run dev (cwd: {FRONTEND})")
        print(f"  PID dir:  {PID_DIR}")
        return

    # Check Ollama
    print("\nChecking Ollama...", end=" ")
    if check_ollama():
        print("✓ running")
    else:
        print("⚠️  not running")
        print("  Start it with: ollama serve")
        print("  The agent will work but LLM calls will fail.\n")

    # Start backend
    print("Starting backend...", end=" ")
    backend_proc = start_backend()
    print(f"PID {backend_proc.pid}")

    # Start frontend
    print("Starting frontend...", end=" ")
    frontend_proc = start_frontend()
    print(f"PID {frontend_proc.pid}")

    # Wait for backend
    print("\nWaiting for backend...", end=" ")
    if wait_for_backend():
        print("✓ ready")
    else:
        print("⚠️  timeout (may still be starting)")

    print("\n" + "=" * 50)
    print("  Frontend:  http://localhost:3000")
    print("  Backend:   http://localhost:8000")
    print("  API Docs:  http://localhost:8000/docs")
    print("=" * 50)
    print("\nPress Ctrl+C to stop all services.")

    try:
        while True:
            # Check if processes are still running
            if backend_proc.poll() is not None:
                print("\n⚠️  Backend stopped unexpectedly")
                break
            if frontend_proc.poll() is not None:
                print("\n⚠️  Frontend stopped unexpectedly")
                break
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nStopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        backend_proc.wait(timeout=5)
        frontend_proc.wait(timeout=5)
        # Clean PID files
        (PID_DIR / "backend.pid").unlink(missing_ok=True)
        (PID_DIR / "frontend.pid").unlink(missing_ok=True)
        print("All services stopped ✓")


if __name__ == "__main__":
    main()
