# Changelog

## v1.0.0-rc.1 (2026-05-12) — Release Candidate

### Security
- **Security Audit**: Full threat model and attack surface analysis (`SECURITY_AUDIT.md`)
- **Security Policy**: Vulnerability reporting and safe usage guidance (`SECURITY.md`)
- **Central Permission System**: `check_command`, `check_file_operation`, `check_network_access`, `check_browser_action`
- **Security Events DB**: All denied/approval-required actions logged with severity
- **SecurityPanel UI**: Real-time security events display
- **Security Scan Script**: `scripts/security_scan.py` detects secrets, keys, forbidden files
- **CI Security Job**: Automated scan on every push/PR
- **Hardened Policies**: Pipe-to-shell blocked, package installs need approval, network commands flagged
- **Termux Hardening**: Safe Mode enforced, extra command restrictions
- **Docker Hardening**: Verified no-privileged, no-socket, non-root, resource limits

### Added
- `GET /api/security/events` - Security event log
- `GET /api/tasks/{id}/security/events` - Per-task security events
- `POST /api/security/check-command` - Pre-check commands
- `POST /api/security/check-path` - Pre-check file paths
- `GET /api/security/policies` - Active security policies

---

## v0.10.0 (2026-05-12) — Termux Support

### Added
- Termux Mode with platform detection
- Android/Termux setup and start scripts
- `GET /api/platform/status` endpoint
- Safe Mode forced on Termux
- Docker/Browser disabled automatically on Termux
- Mobile UI with responsive layout and bottom navigation
- PWA support (manifest, service worker, offline fallback)
- SettingsPanel with platform info and Termux banner

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
- SQLite persistence
- Real-time WebSocket streaming
- GitHub Actions CI
- One-command setup/start scripts
- Tauri Desktop App support
