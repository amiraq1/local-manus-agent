#!/usr/bin/env python3
"""Start Local Manus Agent on Termux."""
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 3000
PID_DIR = ROOT / ".local-manus"
PID_DIR.mkdir(exist_ok=True)
NEXT_PATCHER = ROOT / "scripts" / "patch_next_termux.py"


def port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def wait_for_url(url: str, proc: subprocess.Popen, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def terminate_process(name: str, proc: subprocess.Popen):
    if proc.poll() is not None:
        return
    print(f"Stopping {name}...")
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def cleanup(backend: subprocess.Popen | None, frontend: subprocess.Popen | None):
    if frontend is not None:
        terminate_process("frontend", frontend)
    if backend is not None:
        terminate_process("backend", backend)
    (PID_DIR / "backend.pid").unlink(missing_ok=True)
    (PID_DIR / "frontend.pid").unlink(missing_ok=True)


def main():
    dry_run = "--dry-run" in sys.argv

    print("=" * 50)
    print("Local Manus Agent - Termux Start")
    print("=" * 50)

    if dry_run:
        print("[DRY RUN]\n")
        print(f"Would start backend:  uvicorn app.main:app --host {HOST} --port {BACKEND_PORT}")
        print(f"Would start frontend: npm run dev -- --hostname {HOST} --port {FRONTEND_PORT} (cwd: {FRONTEND})")
        print(f"\nURLs:")
        print(f"  Backend:  http://{HOST}:{BACKEND_PORT}")
        print(f"  Frontend: http://{HOST}:{FRONTEND_PORT}")
        return 0

    # Set Termux env
    env = os.environ.copy()
    env["PLATFORM_MODE"] = "termux"
    env["PYTHONUNBUFFERED"] = "1"

    next_bin = FRONTEND / "node_modules" / ".bin" / "next"
    if not next_bin.exists():
        print("Frontend dependencies are missing.")
        print("Run ./setup-termux.sh first.")
        return 1
    if not NEXT_PATCHER.exists():
        print(f"Missing Next.js patch helper: {NEXT_PATCHER}")
        return 1

    try:
        patch_result = subprocess.run(
            [sys.executable, str(NEXT_PATCHER)],
            cwd=str(ROOT),
            env=env,
            check=False,
        )
    except OSError as exc:
        print(f"Failed to run Next.js Termux patcher: {exc}")
        return 1
    if patch_result.returncode != 0:
        print("Failed to prepare Next.js for Termux.")
        return 1

    if port_in_use(HOST, BACKEND_PORT):
        print(f"Port {BACKEND_PORT} is already in use on {HOST}. Stop the existing backend first.")
        return 1
    if port_in_use(HOST, FRONTEND_PORT):
        print(f"Port {FRONTEND_PORT} is already in use on {HOST}. Stop the existing frontend first.")
        return 1

    print(f"\nStarting backend on {HOST}:{BACKEND_PORT}...")
    backend = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(BACKEND_PORT)],
        cwd=str(BACKEND),
        env=env,
    )
    (PID_DIR / "backend.pid").write_text(str(backend.pid))

    print(f"Starting frontend on {HOST}:{FRONTEND_PORT}...")
    frontend = subprocess.Popen(
        ["npm", "run", "dev", "--", "--hostname", HOST, "--port", str(FRONTEND_PORT)],
        cwd=str(FRONTEND),
        env=env,
    )
    (PID_DIR / "frontend.pid").write_text(str(frontend.pid))

    print("\nWaiting for backend...", end=" ")
    if wait_for_url(f"http://{HOST}:{BACKEND_PORT}/api/health", backend, timeout=20):
        print("✓ ready")
    else:
        print("✗ failed")
        cleanup(backend, frontend)
        return 1

    print("Waiting for frontend...", end=" ")
    if wait_for_url(f"http://{HOST}:{FRONTEND_PORT}", frontend, timeout=60):
        print("✓ ready")
    else:
        print("✗ failed")
        cleanup(backend, frontend)
        return 1

    print("\n" + "=" * 50)
    print(f"  Backend:  http://{HOST}:{BACKEND_PORT}")
    print(f"  Frontend: http://{HOST}:{FRONTEND_PORT}")
    print("=" * 50)
    print("\nPress Ctrl+C to stop.")

    exit_code = 0
    try:
        while True:
            if backend.poll() is not None:
                print("Backend stopped.")
                exit_code = 1
                break
            if frontend.poll() is not None:
                print("Frontend stopped.")
                exit_code = 1
                break
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        cleanup(backend, frontend)
        print("Stopped ✓")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
