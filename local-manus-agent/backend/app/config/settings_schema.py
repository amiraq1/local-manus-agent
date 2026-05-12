"""Settings schema with validation using Pydantic."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class GeneralSettings(BaseModel):
    app_theme: str = "dark"
    language: str = "auto"
    auto_start_preview: bool = True

    @field_validator("language")
    @classmethod
    def validate_language(cls, v):
        if v not in ("ar", "en", "auto"):
            raise ValueError("language must be ar, en, or auto")
        return v


class LLMSettings(BaseModel):
    active_preset: str = "ollama-qwen-coder"
    ollama_base_url: str = "http://localhost:11434"
    litert_runtime: str = "cli"  # cli or sdk
    litert_cli_path: str = ""
    litert_backend: str = "cpu"
    litert_timeout: int = Field(default=180, ge=10, le=3600)
    litert_prompt_mode: str = "temp_file"  # temp_file, stdin, arg
    litert_device: str = "cpu"
    litert_temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    litert_max_tokens: int = Field(default=4096, ge=128, le=32768)
    allow_fallback: bool = True


class SecuritySettings(BaseModel):
    execution_mode: str = "safe"
    require_command_approval: bool = True
    require_file_change_approval: bool = False
    allow_package_installs: bool = False
    allow_network_commands: bool = False

    @field_validator("execution_mode")
    @classmethod
    def validate_mode(cls, v):
        if v not in ("safe", "autonomous"):
            raise ValueError("execution_mode must be safe or autonomous")
        return v


class SandboxSettings(BaseModel):
    enabled: bool = True
    backend: str = "docker"
    image: str = "local-manus-sandbox:latest"
    memory_limit: str = "512m"
    cpu_limit: float = Field(default=1.0, ge=0.1, le=8.0)
    network_enabled: bool = False
    command_timeout: int = Field(default=30, ge=5, le=300)

    @field_validator("memory_limit")
    @classmethod
    def validate_memory(cls, v):
        if not v or not v[-1] in ("m", "g", "M", "G"):
            raise ValueError("memory_limit must end with m or g (e.g. 512m, 2g)")
        return v


class BrowserSettings(BaseModel):
    enabled: bool = True
    allow_external_urls: bool = False
    screenshot_enabled: bool = True
    default_viewport: str = "1280x720"


class MemorySettings(BaseModel):
    enabled: bool = True
    auto_index: bool = True
    auto_summarize: bool = True
    max_index_file_size: int = Field(default=100000, ge=1000, le=10000000)


class TermuxSettings(BaseModel):
    detected: bool = False
    force_safe_mode: bool = True
    browser_mode: str = "disabled"
    host: str = "127.0.0.1"


class AppSettings(BaseModel):
    """Complete application settings."""
    general: GeneralSettings = GeneralSettings()
    llm: LLMSettings = LLMSettings()
    security: SecuritySettings = SecuritySettings()
    sandbox: SandboxSettings = SandboxSettings()
    browser: BrowserSettings = BrowserSettings()
    memory: MemorySettings = MemorySettings()
    termux: TermuxSettings = TermuxSettings()


DEFAULT_SETTINGS = AppSettings().model_dump()


def validate_settings(data: dict) -> tuple[bool, dict, list[str]]:
    """Validate settings data.

    Returns:
        Tuple of (is_valid, validated_data, errors).
    """
    errors = []
    try:
        settings = AppSettings(**data)
        return True, settings.model_dump(), []
    except Exception as e:
        error_str = str(e)
        # Extract field errors
        for line in error_str.split("\n"):
            line = line.strip()
            if line and "value" in line.lower() or "field" in line.lower():
                errors.append(line)
        if not errors:
            errors.append(error_str[:200])
        return False, data, errors


def get_settings_schema() -> dict:
    """Get the JSON schema for settings."""
    return AppSettings.model_json_schema()
