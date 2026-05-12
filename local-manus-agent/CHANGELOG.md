# Changelog

## v1.1.0 (2026-05-12) — Usability & Productivity

### Added
- **Model Manager**: Browse, download, and configure LLM models from the UI
- **Settings UI**: Full structured settings panel with validation (General, Models, Security, Sandbox, Browser, Memory, Termux, About)
- **Export Task as ZIP**: Download all task outputs (files, screenshots, logs, metadata) as a single archive
- **Project Templates**: 6 ready-to-use templates (HTML Landing Page, React Vite, Next.js Dashboard, FastAPI API, Python CLI, Docs Site)
- **Goal Mode**: Describe what you want → auto-analyze → select template → generate → review → preview → export
- Gemma E2B/E4B LiteRT-LM model registry with download instructions
- `user_config.json` persistence (settings survive restarts without editing config.py)
- Pydantic-based settings validation
- `GET /api/settings/schema` for frontend form generation
- `POST /api/settings/reset` to restore defaults
- `POST /api/goals/analyze` and `POST /api/goals/run` endpoints
- `POST /api/tasks/{id}/export` and download endpoints
- `GET /api/templates` and generate endpoints
- GoalModePanel, TemplatesPanel, ModelManagerPanel, SettingsFullPanel, ExportPanel components

### Improved
- LLMStatusPanel now shows preset selector with model availability
- Settings persist in JSON instead of requiring config.py edits
- Better error messages for missing models

---

## v1.0.0 (2026-05-12) — First Stable Release

Production-ready local autonomous agent with multi-agent architecture, security hardening, and full platform support.

## v1.0.0-rc.1 (2026-05-12)

Security hardening release candidate.

## v0.10.0 (2026-05-12)

Termux support, Mobile UI, PWA.

## v0.9.0 (2026-05-12)

First functional release with all core features.
