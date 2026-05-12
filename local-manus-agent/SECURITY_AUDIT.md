# Security Audit Report

**Version**: v0.10.0  
**Date**: 2026-05-12  
**Status**: Pre-v1.0 hardening

## Threat Model

### Actors
- **User**: Trusted, operates the system locally
- **LLM**: Semi-trusted, may produce unexpected outputs
- **External**: Untrusted, should have no access

### Assets
- Host filesystem (outside workspace)
- System credentials and keys
- Network access
- Docker daemon
- User's source code in workspace

## Attack Surface

| Surface | Risk | Mitigation |
|---------|------|------------|
| Shell command execution | High | safety.py + approval flow + sandbox |
| File write operations | Medium | Path validation + workspace isolation |
| Browser automation | Medium | localhost-only + CSP |
| LLM prompt injection | Medium | Output validation + tool restrictions |
| Docker socket | Critical | Explicitly forbidden in policies |
| Network access | Medium | Disabled in sandbox, localhost-only browser |
| PWA cache | Low | No API/task data cached |

## Current Mitigations

### File System
- ✅ Path traversal (`..`) blocked
- ✅ Absolute paths blocked
- ✅ Sensitive patterns blocked (.ssh, .env, keys)
- ✅ Per-task workspace isolation
- ✅ Symlink escape detection

### Command Execution
- ✅ Dangerous commands blocked (rm -rf, sudo, mkfs, etc)
- ✅ Shell injection patterns blocked
- ✅ Pipe-to-shell blocked
- ✅ Safe Mode requires approval
- ✅ Timeout on all commands (30-60s)
- ✅ Docker sandbox available for isolation

### Network
- ✅ Browser limited to localhost by default
- ✅ External URLs require explicit config
- ✅ Sandbox network disabled by default
- ✅ No outbound connections from agent by default

### Docker
- ✅ No privileged mode
- ✅ Docker socket mount forbidden
- ✅ All capabilities dropped
- ✅ Non-root user (UID 1000)
- ✅ Memory/CPU/PID limits
- ✅ Read-only root filesystem
- ✅ Network disabled by default

### Data
- ✅ .env files excluded from indexing
- ✅ Secrets not displayed in UI
- ✅ PWA service worker doesn't cache API responses
- ✅ SQLite DB in .gitignore

## Remaining Limitations

1. **LLM Prompt Injection**: The agent executes plans from LLM output. A sophisticated prompt injection could craft plausible-looking but malicious plans. Mitigation: Safe Mode + SecurityAgent review.

2. **No Rate Limiting**: No rate limiting on API endpoints. Acceptable for local-only use.

3. **No Authentication**: No auth on API/WebSocket. Acceptable for localhost-only deployment.

4. **Workspace Files Readable**: Any file in the task workspace is readable by the agent. Don't put secrets there.

5. **Auto-fix Scope**: Auto-fix modifies files without explicit per-change approval in autonomous mode.

## Recommendations Before v1.0

- [ ] Add optional API authentication for non-localhost deployments
- [ ] Add rate limiting on command execution
- [ ] Add LLM output sanitization layer
- [ ] Add file content scanning before write (detect injected scripts)
- [ ] Add network egress monitoring in sandbox
- [ ] Add integrity checks on workspace files
- [ ] Consider read-only mode for code review without execution
