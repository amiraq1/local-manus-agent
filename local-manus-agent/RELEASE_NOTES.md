# Local Manus Agent v1.0.0

The first stable release of Local Manus Agent — an AI-powered local development agent that runs entirely on your machine.

## Highlights

- 🧠 **Multi-Agent Architecture** — 6 specialized agents coordinated by an orchestrator
- 🤖 **Local LLM** — Ollama with qwen2.5-coder:7b (no cloud API needed)
- 🐳 **Docker Sandbox** — Isolated command execution
- 🌐 **Browser Testing** — Automated visual verification with screenshots
- 📝 **File Diff** — Review changes before they're applied
- 🔍 **Code Review** — Automatic quality checks and fixes
- 🧠 **Memory/RAG** — Remembers context across tasks
- 📱 **Mobile + Termux** — Works on Android via Termux
- 🔒 **Security Hardened** — Audit trail, permission system, blocked patterns

## Installation

```bash
git clone https://github.com/amiraq1/local-manus-agent.git
cd local-manus-agent
python scripts/setup.py
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

## Supported Platforms

| Platform | Status |
|----------|--------|
| Windows 10/11 | ✅ Full support |
| Linux (Ubuntu, Debian, etc) | ✅ Full support |
| macOS | ✅ Full support |
| Android (Termux) | ✅ Lite Mode |
| Docker | ✅ docker-compose |

## Security Notes

- All operations confined to task workspaces
- Safe Mode requires approval for shell commands
- Docker sandbox: non-root, no-privileged, no network by default
- Security events logged for audit
- Automated security scan in CI

## Known Limitations

- LiteRT-LM SDK not yet publicly available (Ollama fallback works)
- No API authentication (designed for localhost only)
- LLM prompt injection mitigated but not fully prevented
- Docker required for sandbox (graceful fallback without it)
- Large models may not run on low-memory devices

## Roadmap After v1.0

- [ ] Full LiteRT-LM integration
- [ ] Git operations (commit, push, branch)
- [ ] Project export as ZIP
- [ ] Multi-model per agent
- [ ] Plugin system
- [ ] Optional API authentication
- [ ] Rate limiting
- [ ] Conversation persistence across sessions
