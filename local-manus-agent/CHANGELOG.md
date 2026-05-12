# Changelog

## v0.10.0 (2026-05-12) — Termux Support

### Added
- **Termux Mode**: Full support for running on Android via Termux
- Platform detection module (`backend/app/platform/`)
- `GET /api/platform/status` endpoint
- `scripts/setup_termux.py` and `scripts/start_termux.py`
- `setup-termux.sh` and `start-termux.sh` shell scripts
- Safe Mode enforced automatically on Termux
- Docker Sandbox disabled automatically on Termux
- Browser Automation disabled by default on Termux
- Extra command restrictions for Termux security
- Remote Ollama support via `OLLAMA_BASE_URL` environment variable
- `PLATFORM_MODE` config option (auto/desktop/termux)

### Changed
- Backend version updated to 0.9.0 → 0.10.0
- Config now includes platform-specific settings

### Security
- Termux always runs in Safe Mode (commands need approval)
- Package install commands (`pkg install`, `pip install`, `npm install -g`) require approval
- Dangerous path operations blocked on Termux

---

## v0.9.0 (2026-05-12) — First Functional Release

### Features
- Multi-Agent Architecture (Orchestrator + 6 specialized agents)
- Ollama + LiteRT-LM provider support with fallback
- Docker Sandbox for isolated command execution
- Browser Automation via Playwright
- Task Workspaces with per-task isolation
- Artifacts system (files, screenshots, reports)
- File Diff with pending/accept/reject flow
- Code Review + Auto Fix
- Agent Memory + Project RAG
- SQLite persistence for all data
- Real-time WebSocket streaming
- GitHub Actions CI
- One-command setup/start scripts
- Tauri Desktop App support

### Infrastructure
- FastAPI backend (Python 3.11+)
- Next.js 14 + React + TypeScript + Tailwind CSS
- Docker Compose support
- Cross-platform scripts (Windows/Linux/macOS)
