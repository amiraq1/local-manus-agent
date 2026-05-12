# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| v0.10.x | ✅ Current |
| < v0.9.0 | ❌ |

## Reporting Vulnerabilities

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email: [create a private security advisory on GitHub](https://github.com/amiraq1/local-manus-agent/security/advisories/new)
3. Include: description, reproduction steps, impact assessment

We will respond within 72 hours.

## Security Assumptions

This project assumes:

- It runs on a **local machine** or **Termux** (not exposed to the internet)
- The user trusts the LLM model they configure
- The workspace directory is the only writable area
- Docker (if used) provides process isolation, not full VM isolation

## Safe Usage Guidance

1. **Always use Safe Mode** when testing untrusted prompts
2. **Review commands** before approving them
3. **Don't expose ports** (8000, 3000) to the public internet
4. **Keep Ollama** on localhost or a trusted network
5. **Don't store secrets** in workspace directories
6. **Use Docker Sandbox** when available for command isolation

## What This Project Does NOT Protect Against

- Malicious LLM outputs that look legitimate (prompt injection)
- Side-channel attacks from the LLM model itself
- Physical access to the device
- Vulnerabilities in Ollama, Docker, or Playwright themselves
- Network attacks if ports are exposed publicly
