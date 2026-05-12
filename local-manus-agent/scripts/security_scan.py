#!/usr/bin/env python3
"""Security scan - checks repo for secrets, sensitive files, and violations."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Patterns that indicate secrets
SECRET_PATTERNS = [
    (r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[=:]\s*['\"][^'\"]{8,}", "Possible API key/secret"),
    (r"(?i)password\s*[=:]\s*['\"][^'\"]{4,}", "Possible hardcoded password"),
    (r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----", "Private key detected"),
    (r"(?i)sk-[a-zA-Z0-9]{20,}", "Possible OpenAI API key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub personal access token"),
    (r"(?i)bearer\s+[a-zA-Z0-9\-._~+/]{20,}", "Bearer token"),
]

# Files that should never be in repo
FORBIDDEN_FILES = [".env", ".env.local", ".env.production"]
FORBIDDEN_EXTENSIONS = [".db", ".sqlite", ".sqlite3", ".pem", ".key"]
FORBIDDEN_DIRS = ["node_modules", ".next", "__pycache__", ".venv", "venv"]

# Files to skip during content scan
SKIP_SCAN = [".png", ".jpg", ".ico", ".woff", ".ttf", ".lock", ".pyc"]


def main():
    print("=" * 50)
    print("Security Scan")
    print("=" * 50)

    issues = []

    # 1. Check for forbidden files
    print("\n[1] Checking for forbidden files...")
    for f in ROOT.rglob("*"):
        if ".git" in f.parts:
            continue
        rel = str(f.relative_to(ROOT))

        if f.name in FORBIDDEN_FILES:
            issues.append(("HIGH", f"Forbidden file: {rel}"))
        if f.suffix in FORBIDDEN_EXTENSIONS and f.is_file():
            issues.append(("HIGH", f"Sensitive file type: {rel}"))

    # 2. Check for forbidden directories
    print("[2] Checking for forbidden directories...")
    for d in ROOT.rglob("*"):
        if not d.is_dir():
            continue
        if ".git" in d.parts:
            continue
        if d.name in FORBIDDEN_DIRS:
            issues.append(("MEDIUM", f"Forbidden directory: {d.relative_to(ROOT)}"))

    # 3. Scan file contents for secrets
    print("[3] Scanning for secrets in source files...")
    for f in ROOT.rglob("*"):
        if not f.is_file():
            continue
        if ".git" in f.parts:
            continue
        if f.suffix in SKIP_SCAN:
            continue
        if any(d in f.parts for d in FORBIDDEN_DIRS):
            continue
        if f.stat().st_size > 500_000:
            continue

        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel = str(f.relative_to(ROOT))
        for pattern, desc in SECRET_PATTERNS:
            if re.search(pattern, content):
                # Skip if it's in a test/example/config template
                if "example" in rel.lower() or "test" in rel.lower() or "template" in rel.lower():
                    continue
                # Skip if it's this scan script itself
                if "security_scan" in rel:
                    continue
                issues.append(("CRITICAL", f"{desc} in {rel}"))

    # 4. Check for docker.sock references
    print("[4] Checking for docker.sock references...")
    for f in ROOT.rglob("*.py"):
        if ".git" in f.parts:
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        if "docker.sock" in content and "FORBIDDEN" not in content and "blocked" not in content.lower():
            if "mount" in content.lower() or "volume" in content.lower():
                issues.append(("HIGH", f"docker.sock reference in {f.relative_to(ROOT)}"))

    # Report
    print("\n" + "=" * 50)
    if not issues:
        print("No security issues found ✓")
        return 0
    else:
        print(f"Found {len(issues)} issue(s):\n")
        for severity, msg in sorted(issues, key=lambda x: {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2}.get(x[0], 3)):
            icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡"}.get(severity, "⚪")
            print(f"  {icon} [{severity}] {msg}")

        critical = sum(1 for s, _ in issues if s == "CRITICAL")
        if critical > 0:
            print(f"\n{critical} CRITICAL issue(s) found. Fix before release.")
            return 1
        print("\nNo critical issues. Review medium/high items.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
