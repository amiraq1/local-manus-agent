#!/usr/bin/env python3
"""Stop Local Manus Agent services."""
import os
import signal
import sys
from pathlib import Path

PID_DIR = Path(__file__).parent.parent / ".local-manus"


def kill_pid(name: str):
    """Kill a process by its PID file."""
    pid_file = PID_DIR / f"{name}.pid"
    if not pid_file.exists():
        print(f"  {name}: no PID file")
        return

    pid = int(pid_file.read_text().strip())
    try:
        if os.name == "nt":
            os.system(f"taskkill /F /PID {pid} >nul 2>&1")
        else:
            os.kill(pid, signal.SIGTERM)
        print(f"  {name}: stopped (PID {pid})")
    except ProcessLookupError:
        print(f"  {name}: already stopped")
    except Exception as e:
        print(f"  {name}: error - {e}")
    finally:
        pid_file.unlink(missing_ok=True)


def main():
    print("Stopping Local Manus Agent...")
    kill_pid("backend")
    kill_pid("frontend")
    print("Done ✓")


if __name__ == "__main__":
    main()
