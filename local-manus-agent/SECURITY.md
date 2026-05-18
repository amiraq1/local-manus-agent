# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| v1.2.x | Current |
| < v1.2.0 | Unsupported |

## Reporting Vulnerabilities

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Create a private security advisory on GitHub
3. Include: description, reproduction steps, impact assessment

We will respond within 72 hours.

## Security Assumptions

This project assumes:

- It runs on a local machine or Termux
- Remote API access is disabled unless explicitly configured
- The user trusts the LLM model they configure
- The workspace directory is the only writable area
- Docker, when enabled, provides process isolation, not full VM isolation

## Safe Usage Guidance

1. Keep Safe Mode enabled when testing untrusted prompts
2. Review commands before approving them
3. Do not expose ports 8000 or 3000 to the public internet
4. Keep Ollama on localhost or a trusted network
5. Do not store secrets in workspace directories
6. Use Docker Sandbox when available for command isolation

## What This Project Does Not Protect Against

- Malicious LLM outputs that look legitimate
- Side-channel attacks from the LLM model itself
- Physical access to the device
- Vulnerabilities in Ollama, Docker, Playwright, or the operating system
- Network attacks if remote access is explicitly enabled without a token
