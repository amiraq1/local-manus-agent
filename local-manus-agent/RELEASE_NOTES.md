# Local Manus Agent v0.9.0

## Overview

First functional release of Local Manus Agent — an AI-powered local development agent that analyzes tasks, creates execution plans, writes code, reviews quality, and verifies results visually, all running locally without external API dependencies.

## Features

| Feature | Description |
|---------|-------------|
| Multi-Agent Architecture | Orchestrator + 6 specialized agents |
| Ollama LLM | Local inference via qwen2.5-coder:7b |
| LiteRT-LM Support | Pluggable provider with fallback |
| Docker Sandbox | Isolated command execution |
| Browser Automation | Playwright-based visual testing |
| File Diff | Unified diffs with approval flow |
| Code Review | Pattern detection + auto-fix |
| Memory/RAG | File indexing + context retrieval |
| Task Workspaces | Per-task isolated directories |
| Artifacts | Tracks files, screenshots, reports |
| Real-time UI | WebSocket streaming + modern React UI |

## Installation

```bash
# Clone
git clone https://github.com/amiraq1/local-manus-agent.git
cd local-manus-agent

# Setup (installs all dependencies)
python scripts/setup.py

# Or manually:
cd backend && pip install -r requirements.txt && playwright install chromium
cd frontend && npm install
```

## Quick Start

```bash
# Start Ollama
ollama pull qwen2.5-coder:7b
ollama serve

# Start the agent
python scripts/start.py

# Open http://localhost:3000
```

Or on Windows: `setup.bat` then `start.bat`

## Requirements

- Python >= 3.11
- Node.js >= 20
- Ollama (for LLM inference)
- Docker (optional, for sandbox)

## Known Limitations

- LiteRT-LM SDK is not yet publicly available; the provider is ready but uses Ollama as fallback
- Docker Sandbox requires Docker to be installed; without it, commands run locally with safety checks
- Preview server timing: browser verification may need a brief delay after preview starts
- Auto-fix is limited to simple patterns (var→let, ==→===, missing alt attributes)
- No Git integration yet (planned for v1.0)
- No project export/ZIP (planned)

## Security Notes

- All file operations are confined to task workspaces
- Path traversal (`..`) and absolute paths are blocked
- Dangerous shell commands are blocked by default
- Docker sandbox runs as non-root with all capabilities dropped
- Docker socket mount is strictly forbidden
- .env files and secrets are excluded from indexing and display
- Safe Mode requires user approval for shell commands and file changes

## Roadmap to v1.0

- [ ] Full LiteRT-LM integration when SDK is available
- [ ] Git operations (commit, push, branch)
- [ ] Project export as ZIP
- [ ] Built-in code editor in UI
- [ ] Plugin system
- [ ] Multi-model support (run different models per agent)
- [ ] Conversation persistence across sessions
