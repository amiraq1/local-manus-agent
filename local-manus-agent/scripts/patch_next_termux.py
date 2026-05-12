#!/usr/bin/env python3
"""Patch installed Next.js SWC loader to prefer wasm on Android/Termux."""

from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
TARGET = ROOT / "frontend" / "node_modules" / "next" / "dist" / "build" / "swc" / "index.js"

ORIGINAL = (
    "const shouldLoadWasmFallbackFirst = !disableWasmFallback && unsupportedPlatform "
    "&& useWasmBinary || isWebContainer;"
)
PATCHED = (
    "const shouldLoadWasmFallbackFirst = !disableWasmFallback && unsupportedPlatform "
    '&& (useWasmBinary || process.platform === "android") || isWebContainer;'
)


def main() -> int:
    if not TARGET.exists():
        print(f"Next.js SWC loader not found: {TARGET}")
        print("Run npm install in frontend first.")
        return 1

    content = TARGET.read_text()
    if PATCHED in content:
        print("Next.js Termux patch already applied.")
        return 0

    if ORIGINAL not in content:
        print(f"Unsupported Next.js SWC loader format in {TARGET}")
        return 1

    TARGET.write_text(content.replace(ORIGINAL, PATCHED, 1))
    print(f"Patched Next.js SWC loader for Termux: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
