# Local Manus Agent v1.2.0

## Overview

`v1.2.0` focuses on making LiteRT-LM usable as a real local runtime and tightening the Android/Termux path. The headline change is a working LiteRT CLI runtime for `.litertlm` models such as Gemma E2B, alongside better diagnostics, Arabic prompt handling, and a more reliable Termux setup/start flow.

## What's New

- LiteRT-LM CLI provider for local `.litertlm` execution
- Gemma E2B support through `litert-lm` CLI
- LiteRT diagnostics with runtime detection for both CLI and Python SDK paths
- Test LiteRT CLI API/UI action for prompt verification
- Prompt transport modes: `temp_file`, `stdin`, and `arg`
- Better preset-selection errors when LiteRT runtime or model files are missing
- Termux-specific backend requirements and automatic Next.js Android SWC patching
- Improved Termux startup lifecycle, cleanup, and health checks
- CORS support for `http://127.0.0.1:3000`

## LiteRT-LM CLI Runtime

Local Manus Agent now prefers the LiteRT CLI runtime when `LLM_PROVIDER` is set to `litert` and the `litert-lm` executable is available. This is particularly useful on Windows, where the Python SDK path may not be available or stable.

Key behaviors:

- Detects `litert-lm` automatically or from configured path
- Supports `.litertlm` model execution without requiring Ollama
- Exposes diagnostics and a test endpoint in the UI
- Falls back more cleanly when runtime or model files are missing

## How to Run Gemma E2B

1. Download the Gemma E2B LiteRT model from Hugging Face after accepting the Gemma license:

```bash
pip install -U huggingface_hub
huggingface-cli login
huggingface-cli download google/gemma-3n-E2B-it-litert-lm gemma-3n-E2B-it-int4.litertlm --local-dir models/gemma-e2b
```

2. Install `uv` if it is not already available.

3. Install LiteRT-LM CLI:

```bash
uv tool install litert-lm
```

4. Test the runtime directly:

```powershell
C:\Users\Aledari\.local\bin\litert-lm.exe run <model> --backend=cpu --prompt "Say hello"
```

5. In Local Manus Agent, open Model Manager and select the Gemma E2B preset or set the model path explicitly.

6. Use `Diagnose LiteRT` and `Test LiteRT CLI` from the UI to verify the runtime.

## Arabic Support

LiteRT CLI prompt handling now includes safer transport modes for non-ASCII prompts, especially Arabic text on Windows consoles.

- `temp_file`: writes UTF-8 prompt to file and passes it safely
- `stdin`: pipes UTF-8 prompt via standard input
- `arg`: passes prompt through `--prompt`, useful for quick ASCII tests

The default path is optimized to reduce Arabic encoding failures.

## Termux Support Improvements

Termux support was hardened in this release:

- `./setup-termux.sh` is now a direct `sh` setup script
- `backend/requirements-termux.txt` is used instead of desktop requirements
- `scripts/patch_next_termux.py` patches Next.js SWC handling on Android
- `./start-termux.sh` now performs better health checks and cleanup
- Verified working URLs:
  - Frontend: `http://127.0.0.1:3000`
  - Backend health: `http://127.0.0.1:8000/api/health`

## Installation

Desktop:

```bash
git clone https://github.com/amiraq1/local-manus-agent.git
cd local-manus-agent
python scripts/setup.py
python scripts/start.py
```

Termux:

```bash
pkg update && pkg install python nodejs git
git clone https://github.com/amiraq1/local-manus-agent.git
cd local-manus-agent
chmod +x setup-termux.sh start-termux.sh
./setup-termux.sh
./start-termux.sh
```

## Upgrade from v1.1.0

```bash
git pull
python scripts/setup.py
```

For Termux users:

```bash
./setup-termux.sh
```

For LiteRT users upgrading from `v1.1.0`:

- Reinstall or verify `litert-lm` CLI
- Re-run dependency installation in `frontend` so the SWC patch can be applied
- Re-check model paths in Model Manager or Settings

## Known Limitations

- LiteRT-LM quality and speed depend on the selected `.litertlm` model and device hardware
- LiteRT Python SDK availability is still environment-dependent; CLI is the more reliable path today
- Termux uses a patched Next.js SWC path for Android rather than upstream native support
- Some webpack cache warnings may still appear during frontend builds without breaking the build
- Browser automation remains disabled by default on Termux

## Roadmap

- [ ] Complete LiteRT-LM end-to-end preset polishing
- [ ] Stronger Windows-first LiteRT setup guidance in UI
- [ ] More model presets for LiteRT CLI runtimes
- [ ] Git integration from the agent UI
- [ ] Plugin system
