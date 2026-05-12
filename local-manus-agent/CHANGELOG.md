# Changelog

## v0.9.0 (2026-05-12) — First Functional Release

The first complete, runnable release of Local Manus Agent.

### Features

- **Multi-Agent Architecture**: Orchestrator coordinates specialized agents (Planner, Coder, Reviewer, Security, Browser, Memory)
- **LLM Providers**: Ollama (primary) + LiteRT-LM (with fallback support)
- **Docker Sandbox**: Isolated command execution with memory/CPU/network limits
- **Browser Automation**: Headless Chromium via Playwright for visual verification and screenshots
- **Task Workspaces**: Per-task isolated file system with artifacts tracking
- **File Diff System**: Unified diffs with pending/accept/reject flow in Safe Mode
- **Code Review + Auto Fix**: Pattern-based review, lint, and automatic fixes for common issues
- **Agent Memory + Project RAG**: File indexing, keyword search, context retrieval, and persistent memories
- **Artifacts System**: Tracks all generated files, screenshots, and reports per task
- **Safe/Autonomous Modes**: Command approval flow in Safe Mode, auto-execution in Autonomous Mode
- **SQLite Persistence**: Tasks, messages, plan steps, tool logs, file changes, artifacts, browser logs, agent steps, memories, file index
- **Real-time WebSocket**: Live streaming of agent phases, tool calls, and multi-agent steps
- **GitHub Actions CI**: Backend compile check, frontend build, Docker image build, security scan
- **One-command Setup**: `python scripts/setup.py` installs everything, `python scripts/start.py` runs all services

### Infrastructure

- FastAPI backend (Python 3.11+)
- Next.js 14 + React + TypeScript + Tailwind CSS frontend
- Docker Compose support
- Cross-platform scripts (Windows .bat, Linux/macOS .sh, Python scripts)

### Security

- Path traversal prevention
- Dangerous command blocking
- Docker socket mount forbidden
- Non-root sandbox containers
- Task workspace isolation
- .env/secrets excluded from indexing
