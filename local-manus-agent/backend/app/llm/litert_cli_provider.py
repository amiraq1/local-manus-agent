"""LiteRT-LM CLI Provider - uses the litert-lm.exe binary to run .litertlm models.

This provider runs the local CLI as a subprocess. Supports three prompt modes
to handle Unicode/Arabic text correctly on Windows:
- temp_file: write prompt to UTF-8 temp file, pass via --prompt-file (safest)
- stdin: pipe prompt via stdin
- arg: pass via --prompt (fails for non-ASCII on Windows consoles)
"""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Optional

from app.llm.base import LocalLLMProvider
from config import LITERT_CONFIG


# Default CLI search paths
_DEFAULT_CLI_PATHS = [
    r"C:\Users\Aledari\.local\bin\litert-lm.exe",
    r"C:\Program Files\litert-lm\litert-lm.exe",
    "/usr/local/bin/litert-lm",
    "/usr/bin/litert-lm",
]


def find_cli(explicit_path: str = "") -> Optional[str]:
    """Find the litert-lm CLI executable."""
    if explicit_path and Path(explicit_path).is_file():
        return explicit_path

    found = shutil.which("litert-lm") or shutil.which("litert-lm.exe")
    if found:
        return found

    for p in _DEFAULT_CLI_PATHS:
        if Path(p).is_file():
            return p

    home = os.environ.get("USERPROFILE") or os.environ.get("HOME")
    if home:
        candidate = Path(home) / ".local" / "bin" / ("litert-lm.exe" if os.name == "nt" else "litert-lm")
        if candidate.is_file():
            return str(candidate)

    return None


def get_cli_version(cli_path: str) -> str:
    """Get CLI version string."""
    try:
        r = subprocess.run([cli_path, "--version"], capture_output=True, text=True, timeout=5, encoding="utf-8", errors="replace")
        if r.returncode == 0:
            return (r.stdout or r.stderr).strip().split("\n")[0]
    except Exception:
        pass
    return "unknown"


def _cli_supports_prompt_file(cli_path: str) -> bool:
    """Check if CLI supports --prompt-file flag."""
    try:
        r = subprocess.run([cli_path, "run", "--help"], capture_output=True, text=True, timeout=5, encoding="utf-8", errors="replace")
        help_text = (r.stdout or "") + (r.stderr or "")
        return "--prompt-file" in help_text or "prompt_file" in help_text
    except Exception:
        return False


class LiteRTCLIProvider(LocalLLMProvider):
    """LiteRT-LM provider using the CLI subprocess."""

    def __init__(self):
        self.model_path = LITERT_CONFIG.get("model_path", "")
        self.temperature = LITERT_CONFIG.get("temperature", 0.7)
        self.max_tokens = LITERT_CONFIG.get("max_tokens", 4096)
        self.backend = LITERT_CONFIG.get("backend", "cpu")
        self.cli_path = LITERT_CONFIG.get("cli_path", "")
        self.timeout = int(LITERT_CONFIG.get("timeout", 180))
        self.prompt_mode = "temp_file"  # temp_file, stdin, arg

        # Load from user_config
        try:
            from app.user_config_manager import load_user_config
            cfg = load_user_config()
            llm_cfg = cfg.get("llm", {})
            self.cli_path = self.cli_path or llm_cfg.get("litert_cli_path", "")
            self.backend = llm_cfg.get("litert_backend", self.backend)
            self.timeout = int(llm_cfg.get("litert_timeout", self.timeout))
            self.prompt_mode = llm_cfg.get("litert_prompt_mode", self.prompt_mode)
            if not self.model_path:
                mp = cfg.get("model_paths", {}).get("gemma-e2b-litert", "")
                if mp:
                    self.model_path = mp
        except Exception:
            pass

        self._resolved_cli = find_cli(self.cli_path)
        # Cache whether CLI supports --prompt-file
        self._supports_prompt_file: Optional[bool] = None

    def _check_prompt_file_support(self) -> bool:
        """Check (once) if CLI supports --prompt-file."""
        if self._supports_prompt_file is None and self._resolved_cli:
            self._supports_prompt_file = _cli_supports_prompt_file(self._resolved_cli)
        return bool(self._supports_prompt_file)

    def is_available(self) -> bool:
        if not self._resolved_cli:
            return False
        if not self.model_path or not Path(self.model_path).exists():
            return False
        return True

    def model_info(self) -> dict:
        cli_exists = bool(self._resolved_cli)
        model_exists = bool(self.model_path and Path(self.model_path).exists())

        info = {
            "provider": "litert_cli",
            "runtime": "cli",
            "cli_path": self._resolved_cli or "",
            "cli_available": cli_exists,
            "model_path": self.model_path,
            "model_exists": model_exists,
            "backend": self.backend,
            "timeout": self.timeout,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "prompt_mode": self.prompt_mode,
            "supports_prompt_file": self._check_prompt_file_support() if cli_exists else False,
            "available": self.is_available(),
        }

        if cli_exists:
            info["cli_version"] = get_cli_version(self._resolved_cli)

        if cli_exists and model_exists:
            info["status_code"] = "ready_cli"
        elif cli_exists and not model_exists:
            info["status_code"] = "cli_ready_model_missing"
            info["error"] = "CLI found, but model file missing"
        elif not cli_exists and model_exists:
            info["status_code"] = "model_ready_cli_missing"
            info["error"] = "Model file found, but litert-lm CLI not installed"
        else:
            info["status_code"] = "not_configured"
            info["error"] = "Neither CLI nor model available"

        return info

    def _messages_to_prompt(self, messages) -> str:
        """Convert messages to a single prompt string."""
        if isinstance(messages, str):
            return messages
        if isinstance(messages, list):
            parts = []
            for m in messages:
                if isinstance(m, dict):
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    parts.append(f"{role}: {content}")
                else:
                    parts.append(str(m))
            return "\n".join(parts)
        return str(messages)

    def _make_env(self) -> dict:
        """Build environment with UTF-8 forced."""
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["LANG"] = env.get("LANG") or "en_US.UTF-8"
        return env

    def _run_cli_with_temp_file(self, prompt: str) -> dict:
        """Run CLI with prompt written to a UTF-8 temp file."""
        # Try --prompt-file if supported
        use_prompt_file_flag = self._check_prompt_file_support()

        tmp = tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=".txt", delete=False
        )
        tmp.write(prompt)
        tmp.close()

        try:
            if use_prompt_file_flag:
                cmd = [self._resolved_cli, "run", self.model_path, f"--backend={self.backend}", "--prompt-file", tmp.name]
            else:
                # CLI doesn't support --prompt-file, fall back to --prompt with proper encoding
                cmd = [self._resolved_cli, "run", self.model_path, f"--backend={self.backend}", "--prompt", prompt]

            r = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout,
                env=self._make_env(),
            )
            # Decode output manually with UTF-8
            stdout = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
            stderr = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""

            return {
                "success": r.returncode == 0,
                "output": stdout.strip(),
                "stderr": stderr.strip(),
                "returncode": r.returncode,
                "method": "prompt-file" if use_prompt_file_flag else "prompt-arg",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {self.timeout}s", "output": "", "stderr": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "output": "", "stderr": ""}
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    def _run_cli_with_stdin(self, prompt: str) -> dict:
        """Run CLI piping prompt via stdin."""
        cmd = [self._resolved_cli, "run", self.model_path, f"--backend={self.backend}"]

        try:
            r = subprocess.run(
                cmd,
                input=prompt.encode("utf-8"),
                capture_output=True,
                timeout=self.timeout,
                env=self._make_env(),
            )
            stdout = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
            stderr = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""

            return {
                "success": r.returncode == 0,
                "output": stdout.strip(),
                "stderr": stderr.strip(),
                "returncode": r.returncode,
                "method": "stdin",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {self.timeout}s", "output": "", "stderr": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "output": "", "stderr": ""}

    def _run_cli_with_arg(self, prompt: str) -> dict:
        """Run CLI with --prompt argument (may fail for non-ASCII on Windows)."""
        cmd = [self._resolved_cli, "run", self.model_path, f"--backend={self.backend}", "--prompt", prompt]

        try:
            r = subprocess.run(
                cmd,
                capture_output=True,
                timeout=self.timeout,
                env=self._make_env(),
            )
            stdout = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
            stderr = r.stderr.decode("utf-8", errors="replace") if r.stderr else ""

            return {
                "success": r.returncode == 0,
                "output": stdout.strip(),
                "stderr": stderr.strip(),
                "returncode": r.returncode,
                "method": "prompt-arg",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {self.timeout}s", "output": "", "stderr": ""}
        except Exception as e:
            return {"success": False, "error": str(e), "output": "", "stderr": ""}

    def _run_cli(self, prompt: str) -> dict:
        """Run the CLI using the configured prompt mode."""
        if not self._resolved_cli:
            return {"success": False, "error": "CLI not found", "output": "", "stderr": ""}
        if not self.model_path or not Path(self.model_path).exists():
            return {"success": False, "error": "Model file not found", "output": "", "stderr": ""}

        mode = self.prompt_mode
        if mode == "stdin":
            result = self._run_cli_with_stdin(prompt)
        elif mode == "arg":
            result = self._run_cli_with_arg(prompt)
        else:  # temp_file (default)
            result = self._run_cli_with_temp_file(prompt)

        # If temp_file failed and prompt has non-ASCII, try stdin as fallback
        if not result.get("success") and mode == "temp_file":
            has_unicode = any(ord(c) > 127 for c in prompt)
            if has_unicode:
                stdin_result = self._run_cli_with_stdin(prompt)
                if stdin_result.get("success"):
                    return stdin_result

        return result

    async def generate(self, prompt, **kwargs) -> str:
        """Generate a response via the CLI."""
        prompt_text = self._messages_to_prompt(prompt)
        result = self._run_cli(prompt_text)
        if result["success"]:
            return result["output"]
        raise RuntimeError(result.get("error") or result.get("stderr") or "CLI run failed")

    async def stream(self, prompt, **kwargs) -> AsyncGenerator[str, None]:
        """Stream - yields full output as one chunk (CLI has no native streaming)."""
        text = await self.generate(prompt, **kwargs)
        if text:
            yield text

    def tool_call_parse(self, response: str) -> dict | None:
        """Parse a tool call JSON from response."""
        try:
            text = response.strip()
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                parsed = json.loads(text[start:end])
                if "tool" in parsed and "params" in parsed:
                    return parsed
        except (json.JSONDecodeError, KeyError):
            pass
        return None

    def run_with_method(self, prompt: str, method: str = "temp_file") -> dict:
        """Run CLI with a specific method (for testing/diagnostics)."""
        if not self._resolved_cli or not self.model_path:
            return {"success": False, "error": "Provider not configured"}

        if method == "stdin":
            return self._run_cli_with_stdin(prompt)
        elif method == "arg":
            return self._run_cli_with_arg(prompt)
        else:
            return self._run_cli_with_temp_file(prompt)
