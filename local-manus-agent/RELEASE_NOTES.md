# Local Manus Agent v1.1.0

## Overview

This release focuses on usability and productivity — making it easier to manage models, configure settings, generate projects from templates, and export results.

## What's New

### Model Manager
- Browse all supported models (Ollama, Gemma E2B, Gemma E4B, Custom LiteRT)
- See status: Ready / Missing / SDK Missing
- Copy download commands for Hugging Face models
- Set custom model paths from the UI
- Persistent configuration in `user_config.json`

### Settings UI
- Full settings panel with 8 tabs (General, Models, Security, Sandbox, Browser, Memory, Termux, About)
- Pydantic validation with clear error messages
- Save/Reset buttons with unsaved changes indicator
- Termux-locked options with explanations

### Export Task as ZIP
- Download all task outputs as a single ZIP file
- Includes: files, screenshots, logs, summary.md, metadata.json
- Excludes: .env, .db, node_modules, large files
- Registered as artifact (type: archive)

### Project Templates
- 6 templates: HTML Landing Page, React Vite, Next.js Dashboard, FastAPI API, Python CLI, Docs Site
- Variable substitution (project_name, description, primary_color)
- Security: path traversal blocked, script injection sanitized

### Goal Mode
- Describe a goal in natural language
- Auto-analyzes project type and recommends template
- Generates project, runs review, starts preview, creates export
- End-to-end in one click

## Installation

```bash
git clone https://github.com/amiraq1/local-manus-agent.git
cd local-manus-agent
python scripts/setup.py
python scripts/start.py
```

## Upgrade from v1.0.0

```bash
git pull
python scripts/setup.py  # updates dependencies if needed
python scripts/start.py
```

No breaking changes. Database migrations are automatic.

## Known Limitations

- Goal Mode uses keyword matching (no LLM needed), but results are template-based
- LiteRT-LM SDK not yet publicly available (Ollama fallback works)
- Export ZIP doesn't include node_modules or build outputs
- Templates are static (no LLM-generated content in this mode)

## Roadmap

- [ ] Git integration (commit, push from agent)
- [ ] Custom template creation from UI
- [ ] LLM-powered goal analysis (when Ollama is available)
- [ ] Collaborative mode
- [ ] Plugin system
