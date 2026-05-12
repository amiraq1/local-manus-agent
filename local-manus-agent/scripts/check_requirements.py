#!/usr/bin/env python3
"""Check system requirements for Local Manus Agent."""
import subprocess
import sys
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent


def run(cmd: list[str], timeout: int = 10) -> tuple[bool, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, r.stdout.strip()
    except FileNotFoundError:
        return False, ""
    except Exception as e:
        return False, str(e)


def check_python():
    v = sys.version_info
    ok = v >= (3, 11)
    ver = f"{v.major}.{v.minor}.{v.micro}"
    return ok, ver, "Python >= 3.11" if not ok else ""


def check_node():
    ok, out = run(["node", "--version"])
    if not ok:
        return False, "", "Node.js not found"
    ver = out.lstrip("v")
    major = int(ver.split(".")[0]) if ver else 0
    return major >= 20, ver, "" if major >= 20 else "Node.js >= 20 required"


def check_npm():
    ok, out = run(["npm", "--version"])
    if not ok and os.name == "nt":
        ok, out = run(["npm.cmd", "--version"])
    return ok, out, "" if ok else "npm not found"


def check_git():
    ok, out = run(["git", "--version"])
    return ok, out.replace("git version ", ""), "" if ok else "git not found"


def check_docker():
    ok, out = run(["docker", "--version"])
    ver = out.split(",")[0].replace("Docker version ", "") if ok else ""
    return ok, ver, ""


def check_ollama():
    ok, out = run(["ollama", "--version"])
    return ok, out, ""


def check_playwright():
    ok, _ = run([sys.executable, "-m", "playwright", "--version"])
    return ok, "", ""


def check_file(path: str):
    return (ROOT / path).exists()


def main():
    print("=" * 50)
    print("Local Manus Agent - Requirements Check")
    print("=" * 50)

    results = []

    # Required
    ok, ver, msg = check_python()
    results.append(("Python >= 3.11", ok, ver, True, msg))

    ok, ver, msg = check_node()
    results.append(("Node.js >= 20", ok, ver, True, msg))

    ok, ver, msg = check_npm()
    results.append(("npm", ok, ver, True, msg))

    ok, ver, msg = check_git()
    results.append(("git", ok, ver, True, msg))

    # Optional
    ok, ver, msg = check_docker()
    results.append(("Docker", ok, ver, False, msg))

    ok, ver, msg = check_ollama()
    results.append(("Ollama", ok, ver, False, msg))

    ok, ver, msg = check_playwright()
    results.append(("Playwright", ok, ver, False, msg))

    # Files
    results.append(("backend/requirements.txt", check_file("backend/requirements.txt"), "", True, ""))
    results.append(("frontend/package.json", check_file("frontend/package.json"), "", True, ""))

    print()
    all_ok = True
    for name, ok, ver, required, msg in results:
        if ok:
            icon = "✅"
        elif required:
            icon = "❌"
            all_ok = False
        else:
            icon = "⚠️ "

        line = f"  {icon} {name}"
        if ver:
            line += f" ({ver})"
        if not ok and msg:
            line += f" - {msg}"
        elif not ok and not required:
            line += " - optional, not found"
        print(line)

    print()
    if all_ok:
        print("All required dependencies are available ✓")
    else:
        print("Some required dependencies are missing ✗")
        print("Install them before running setup.")
        sys.exit(1)

    return all_ok


if __name__ == "__main__":
    main()
