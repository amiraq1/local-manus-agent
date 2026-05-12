# Local Manus Agent v0.10.0

## Overview

This release adds full Termux (Android) support, allowing Local Manus Agent to run on mobile devices with appropriate security adaptations.

## New: Termux Support

Local Manus Agent now detects when running inside Termux and automatically adapts:

- **Docker Sandbox**: Disabled (not available on Android)
- **Browser Automation**: Disabled by default
- **Safe Mode**: Always enforced (all commands need approval)
- **Extra Security**: Package install commands require explicit approval

### Installation on Android

```bash
# Install Termux from F-Droid (recommended)
pkg update && pkg install python nodejs git

git clone https://github.com/amiraq1/local-manus-agent
cd local-manus-agent
chmod +x setup-termux.sh start-termux.sh

./setup-termux.sh
./start-termux.sh
```

### Using Remote Ollama

Since running large LLMs on a phone is impractical, connect to Ollama on your PC:

```bash
# On your PC: ollama serve (ensure it listens on 0.0.0.0)
# On Termux:
export OLLAMA_BASE_URL=http://<your-pc-ip>:11434
./start-termux.sh
```

## Other Changes

- Added `GET /api/platform/status` endpoint
- Platform detection module for auto-configuration
- Config: `PLATFORM_MODE`, `TERMUX_*` settings

## Limitations on Termux

- Docker Sandbox unavailable
- Browser Automation unavailable by default
- Large models may not fit in device memory
- Performance depends on device hardware
- Recommended: use remote Ollama

## Security Notes

- Safe Mode is always active on Termux
- Commands like `pkg install`, `pip install`, `npm install -g` need approval
- All standard safety checks still apply
- Task workspace isolation is maintained

## Upgrade from v0.9.0

No breaking changes. Simply `git pull` and restart:

```bash
git pull
python scripts/setup.py  # or ./setup-termux.sh on Android
python scripts/start.py  # or ./start-termux.sh on Android
```
