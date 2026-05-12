# Local Manus Agent v1.0.0-rc.1

> ⚠️ This is a **Release Candidate**. It is feature-complete for v1.0 but may contain issues discovered during testing.

## Overview

First release candidate for v1.0. This release focuses on security hardening after the full feature set was completed in v0.9.0 and v0.10.0.

## What's New (since v0.10.0)

### Security Hardening
- Central permission system with `allow/deny/require_approval` decisions
- Security events database with severity tracking
- Automated security scan in CI pipeline
- Hardened command blocking (regex-based pattern matching)
- Package install commands require explicit approval
- Network commands flagged for review
- Pipe-to-shell patterns blocked
- SecurityPanel in frontend for monitoring

### Documentation
- `SECURITY.md` - Vulnerability reporting and safe usage
- `SECURITY_AUDIT.md` - Threat model, attack surface, mitigations

## Installation

```bash
git clone https://github.com/amiraq1/local-manus-agent.git
cd local-manus-agent
python scripts/setup.py
python scripts/start.py
```

## Upgrade from v0.10.0

```bash
git pull
# Database migrations are automatic (new tables created on startup)
python scripts/start.py
```

## Known Limitations

- LLM prompt injection is mitigated but not fully prevented (Safe Mode recommended)
- No API authentication (localhost-only assumption)
- No rate limiting on endpoints
- LiteRT-LM SDK not yet publicly available (Ollama fallback works)
- Docker required for sandbox (graceful fallback without it)

## Testing Checklist Before v1.0

- [ ] Run full task in Safe Mode with approval flow
- [ ] Run full task in Autonomous Mode
- [ ] Verify security scan passes on clean repo
- [ ] Test on Termux (Android)
- [ ] Test PWA install on mobile
- [ ] Test Docker Sandbox with real Docker
- [ ] Verify all API endpoints respond correctly
- [ ] Test WebSocket agent flow end-to-end with Ollama
- [ ] Review all security events are logged properly
- [ ] Confirm no secrets in repo

## Security Notes

- All file operations confined to task workspaces
- Dangerous commands blocked by default
- Safe Mode requires user approval for shell commands
- Docker sandbox runs non-root with all capabilities dropped
- External URLs blocked in browser automation by default
- Security events logged for audit trail
