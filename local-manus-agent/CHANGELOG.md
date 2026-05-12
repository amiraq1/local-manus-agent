# Changelog

## v1.0.0 (2026-05-12) — First Stable Release

Production-ready local autonomous agent foundation.

### Core
- **Multi-Agent Orchestration**: Orchestrator + PlannerAgent, CoderAgent, ReviewerAgent, SecurityAgent, BrowserAgent, MemoryAgent
- **Local LLM Providers**: Ollama (primary) + LiteRT-LM (with fallback)
- **Docker Sandbox**: Isolated command execution with resource limits
- **Browser Automation**: Headless Chromium via Playwright for visual verification
- **Task Workspaces**: Per-task isolated directories with artifacts tracking
- **File Diff System**: Unified diffs with pending/accept/reject approval flow
- **Code Review + Auto Fix**: Pattern detection, lint, and automatic fixes
- **Agent Memory + Project RAG**: File indexing, keyword search, context retrieval
- **Artifacts System**: Tracks files, screenshots, and reports per task

### Platform
- **Termux Lite Mode**: Full Android support with platform detection and adaptations
- **Mobile UI + PWA**: Responsive layout, bottom navigation, installable web app
- **Desktop App**: Tauri scaffold for native Windows/Linux/macOS builds
- **One-command Scripts**: `setup.py`, `start.py`, `stop.py`, `dev.py`
- **Cross-platform**: Windows (.bat), Linux/macOS (.sh), Termux scripts

### Security
- Central permission system (allow/deny/require_approval)
- Security events database with audit trail
- Automated security scan in CI
- Path traversal, shell injection, and secrets access blocked
- Docker: no-privileged, no-socket, non-root, resource limits
- Termux: Safe Mode enforced, extra command restrictions
- SECURITY.md and SECURITY_AUDIT.md

### Infrastructure
- FastAPI backend (Python 3.11+)
- Next.js 14 + React + TypeScript + Tailwind CSS
- SQLite persistence (10 tables)
- Real-time WebSocket streaming
- GitHub Actions CI (backend, frontend, Docker, security)
- Docker Compose support

---

## v1.0.0-rc.1 (2026-05-12)

Security hardening release candidate.

## v0.10.0 (2026-05-12)

Termux support, Mobile UI, PWA.

## v0.9.0 (2026-05-12)

First functional release with all core features.
