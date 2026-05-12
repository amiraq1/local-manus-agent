"""Main FastAPI application for Local Manus Agent."""
import asyncio
import json
import uuid
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from pydantic import BaseModel

from app.agent.agent import Agent
from app.tools.file_tools import read_file, write_file, edit_file, list_files, create_folder
from app.tools.shell_tools import run_command
from app.tools.preview_tools import start_preview, stop_preview, get_preview_url
from app.browser.session import get_browser_manager
from app import database as db
from config import EXECUTION_MODE

app = FastAPI(title="Local Manus Agent", version="0.9.0")

# Apply Termux adaptations if detected
from app.platform.detector import is_termux
if is_termux():
    from app.platform.termux import apply_termux_config
    apply_termux_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store active WebSocket connections per task for approval flow
active_connections: dict[str, WebSocket] = {}
# Store approval events for synchronization
approval_events: dict[int, asyncio.Event] = {}
approval_results: dict[int, bool] = {}


class TaskRequest(BaseModel):
    message: str
    task_id: Optional[str] = None


class FileWriteRequest(BaseModel):
    path: str
    content: str


class CommandRequest(BaseModel):
    command: str


class ModeRequest(BaseModel):
    mode: str  # "safe" or "autonomous"


# --- Health & Info ---

@app.get("/")
async def root():
    return {"status": "running", "service": "Local Manus Agent", "version": "2.0.0"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/mode")
async def get_mode():
    """Get current execution mode."""
    return {"mode": EXECUTION_MODE}


@app.post("/api/mode")
async def set_mode(request: ModeRequest):
    """Set execution mode."""
    global EXECUTION_MODE
    import config
    if request.mode not in ("safe", "autonomous"):
        return {"error": "Invalid mode. Use 'safe' or 'autonomous'."}
    config.EXECUTION_MODE = request.mode
    return {"mode": request.mode}


# --- Tasks ---

@app.get("/api/tasks")
async def get_tasks():
    """Get all tasks history."""
    tasks = db.get_all_tasks()
    return {"tasks": tasks}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get a single task with full details."""
    task = db.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    return task


# --- Approvals ---

@app.get("/api/approvals")
async def get_approvals():
    """Get all pending approvals."""
    approvals = db.get_pending_approvals()
    return {"approvals": approvals}


@app.post("/api/tasks/{task_id}/approve")
async def approve_command(task_id: str, body: dict = {}):
    """Approve a pending command for a task."""
    approval_id = body.get("approval_id")
    if not approval_id:
        # Find the latest pending approval for this task
        approvals = db.get_pending_approvals(task_id)
        if not approvals:
            return {"error": "No pending approvals for this task"}
        approval_id = approvals[0]["id"]

    db.resolve_approval(approval_id, approved=True)
    # Signal the waiting agent
    if approval_id in approval_events:
        approval_results[approval_id] = True
        approval_events[approval_id].set()
    return {"status": "approved", "approval_id": approval_id}


@app.post("/api/tasks/{task_id}/reject")
async def reject_command(task_id: str, body: dict = {}):
    """Reject a pending command for a task."""
    approval_id = body.get("approval_id")
    if not approval_id:
        approvals = db.get_pending_approvals(task_id)
        if not approvals:
            return {"error": "No pending approvals for this task"}
        approval_id = approvals[0]["id"]

    db.resolve_approval(approval_id, approved=False)
    # Signal the waiting agent
    if approval_id in approval_events:
        approval_results[approval_id] = False
        approval_events[approval_id].set()
    return {"status": "rejected", "approval_id": approval_id}


# --- Files ---

@app.get("/api/files")
async def get_files():
    """List all files in workspace."""
    result = list_files()
    return {"files": result}


@app.post("/api/files/read")
async def api_read_file(request: dict):
    """Read a file from workspace."""
    path = request.get("path", "")
    result = read_file(path)
    return result


@app.post("/api/files/write")
async def api_write_file(request: FileWriteRequest):
    """Write a file to workspace."""
    result = write_file(request.path, request.content)
    return result


# --- Commands ---

@app.post("/api/command")
async def api_run_command(request: CommandRequest):
    """Run a command in workspace."""
    result = run_command(request.command)
    return result


# --- Preview ---

@app.get("/api/preview/url")
async def api_preview_url():
    """Get preview server URL."""
    return get_preview_url()


@app.post("/api/preview/start")
async def api_start_preview(body: dict = {}):
    """Start preview server for a task."""
    from app.workspace.manager import set_current_task_id
    task_id = body.get("task_id")
    if task_id:
        set_current_task_id(task_id)
    return start_preview()


@app.post("/api/preview/stop")
async def api_stop_preview():
    """Stop preview server."""
    return stop_preview()


# --- File Changes / Diff ---

@app.get("/api/changes")
async def get_all_changes(status: Optional[str] = None):
    """Get all file changes, optionally filtered by status."""
    changes = db.list_file_changes(status=status)
    return {"changes": changes}


@app.get("/api/tasks/{task_id}/changes")
async def get_task_changes(task_id: str):
    """Get file changes for a specific task."""
    changes = db.list_file_changes(task_id=task_id)
    return {"changes": changes}


@app.get("/api/tasks/{task_id}/changes/{change_id}")
async def get_single_change(task_id: str, change_id: str):
    """Get a single file change with isolation check."""
    change = db.get_file_change(change_id)
    if not change:
        return {"error": "Change not found"}
    if change["task_id"] != task_id:
        return {"error": "Change does not belong to this task"}
    return change


@app.post("/api/tasks/{task_id}/changes/{change_id}/accept")
async def api_accept_change(task_id: str, change_id: str):
    """Accept a pending file change with task isolation."""
    change = db.get_file_change(change_id)
    if not change:
        return {"error": "Change not found"}
    if change["task_id"] != task_id:
        return {"error": "Change does not belong to this task"}
    from app.tools.diff_tools import accept_file_change as do_accept
    return do_accept(change_id)


@app.post("/api/tasks/{task_id}/changes/{change_id}/reject")
async def api_reject_change(task_id: str, change_id: str):
    """Reject a pending file change with task isolation."""
    change = db.get_file_change(change_id)
    if not change:
        return {"error": "Change not found"}
    if change["task_id"] != task_id:
        return {"error": "Change does not belong to this task"}
    from app.tools.diff_tools import reject_file_change as do_reject
    return do_reject(change_id)


@app.post("/api/tasks/{task_id}/changes/{change_id}/apply")
async def api_apply_change(task_id: str, change_id: str):
    """Apply a file change with task isolation."""
    change = db.get_file_change(change_id)
    if not change:
        return {"error": "Change not found"}
    if change["task_id"] != task_id:
        return {"error": "Change does not belong to this task"}
    from app.tools.diff_tools import accept_file_change as do_accept
    return do_accept(change_id)


# --- Code Review ---

@app.post("/api/tasks/{task_id}/review")
async def api_review_code(task_id: str, body: dict = {}):
    """Review a file for code quality issues."""
    from app.tools.code_review_tools import review_code as do_review
    path = body.get("path", "")
    if not path:
        return {"error": "path is required"}
    return do_review(task_id, path)


@app.post("/api/tasks/{task_id}/checks")
async def api_project_checks(task_id: str):
    """Run project-level checks."""
    from app.tools.code_review_tools import run_project_checks
    return run_project_checks(task_id)


@app.post("/api/tasks/{task_id}/auto-fix")
async def api_autofix(task_id: str, body: dict = {}):
    """Auto-fix simple issues in a file."""
    from app.tools.code_review_tools import auto_fix as do_fix
    path = body.get("path", "")
    if not path:
        return {"error": "path is required"}
    return do_fix(task_id, path)


# --- LLM Provider ---

@app.get("/api/platform/status")
async def api_platform_status():
    """Get platform detection status."""
    from app.platform.detector import get_platform_status
    return get_platform_status()


# --- Security ---

@app.get("/api/security/events")
async def api_security_events(limit: int = 50):
    """Get recent security events."""
    from app.security.audit_log import get_security_events
    return {"events": get_security_events(limit=limit)}


@app.get("/api/tasks/{task_id}/security/events")
async def api_task_security_events(task_id: str):
    """Get security events for a task."""
    from app.security.audit_log import get_security_events
    return {"events": get_security_events(task_id=task_id)}


@app.post("/api/security/check-command")
async def api_check_command(body: dict):
    """Check if a command would be allowed."""
    from app.security.permissions import check_command
    command = body.get("command", "")
    task_id = body.get("task_id", "")
    decision, reason = check_command(task_id, command)
    return {"command": command, "decision": decision.value, "reason": reason}


@app.post("/api/security/check-path")
async def api_check_path(body: dict):
    """Check if a file path would be allowed."""
    from app.security.permissions import check_file_operation
    path = body.get("path", "")
    operation = body.get("operation", "read")
    task_id = body.get("task_id", "")
    decision, reason = check_file_operation(task_id, path, operation)
    return {"path": path, "operation": operation, "decision": decision.value, "reason": reason}


@app.get("/api/security/policies")
async def api_security_policies():
    """Get active security policies."""
    from app.security.policies import get_active_policies
    return get_active_policies()


@app.get("/api/llm/status")
async def api_llm_status():
    """Get LLM provider status."""
    from app.llm.factory import get_provider_status
    return get_provider_status()


@app.get("/api/llm/litert/diagnostics")
async def api_litert_diagnostics():
    """Get comprehensive LiteRT-LM diagnostics."""
    from app.llm.litert_diagnostics import get_full_diagnostics
    from app.user_config_manager import load_user_config
    import config

    # Get best known model path
    cfg = load_user_config()
    model_path = (
        cfg.get("model_paths", {}).get("gemma-e2b-litert", "")
        or config.GEMMA_E2B_LITERT_MODEL_PATH
        or config.LITERT_CONFIG.get("model_path", "")
    )

    # Fallback to recommended if still empty
    if not model_path:
        from app.llm.model_registry import MODEL_REGISTRY
        rec = MODEL_REGISTRY.get("gemma-e2b-litert", {}).get("recommended_path", "")
        from pathlib import Path as _P
        if rec and _P(rec).exists():
            model_path = rec

    device = cfg.get("litert_device", "cpu")
    return get_full_diagnostics(model_path, device)


@app.post("/api/llm/litert/test-cli")
async def api_litert_test_cli(body: dict):
    """Test LiteRT-LM CLI with a prompt."""
    from app.llm.litert_cli_provider import LiteRTCLIProvider
    from app.user_config_manager import load_user_config
    import config

    prompt = body.get("prompt", "اكتب جملة قصيرة بالعربية")

    # Ensure model path is set
    cfg = load_user_config()
    model_path = (
        cfg.get("model_paths", {}).get("gemma-e2b-litert", "")
        or config.GEMMA_E2B_LITERT_MODEL_PATH
    )
    if not model_path:
        from app.llm.model_registry import MODEL_REGISTRY
        from pathlib import Path as _P
        rec = MODEL_REGISTRY.get("gemma-e2b-litert", {}).get("recommended_path", "")
        if rec and _P(rec).exists():
            model_path = rec

    if model_path:
        config.LITERT_CONFIG["model_path"] = model_path

    provider = LiteRTCLIProvider()
    info = provider.model_info()
    if not provider.is_available():
        return {"success": False, "error": info.get("error", "CLI not available"), "info": info}

    try:
        output = await provider.generate(prompt)
        return {"success": True, "output": output, "runtime": "cli", "info": info}
    except Exception as e:
        return {"success": False, "error": str(e), "info": info}


@app.post("/api/llm/test")
async def api_llm_test():
    """Test the LLM provider with a simple prompt."""
    try:
        from app.llm.factory import get_llm_provider
        provider = get_llm_provider()
        if not provider.is_available():
            return {"success": False, "error": "Provider not available", "info": provider.model_info()}
        result = await provider.generate("Say hello in one word.")
        return {"success": True, "response": result[:200], "info": provider.model_info()}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/llm/presets")
async def api_llm_presets():
    """Get available LLM presets."""
    from config import LLM_PRESETS, ACTIVE_LLM_PRESET, GEMMA_E2B_LITERT_MODEL_PATH
    presets = []
    for key, preset in LLM_PRESETS.items():
        p = {**preset, "id": key, "active": key == ACTIVE_LLM_PRESET}
        # Check model availability for litert presets
        if preset["provider"] == "litert":
            model_path = ""
            if key == "gemma-e2b-litert":
                model_path = GEMMA_E2B_LITERT_MODEL_PATH
            elif key == "litert-custom":
                from config import LITERT_CONFIG
                model_path = LITERT_CONFIG.get("model_path", "")
            p["model_path"] = model_path
            p["model_available"] = bool(model_path and Path(model_path).exists())
        else:
            p["model_available"] = True
        presets.append(p)
    return {"presets": presets, "active": ACTIVE_LLM_PRESET}


@app.post("/api/llm/select-preset")
async def api_select_preset(body: dict):
    """Select an LLM preset."""
    import config
    from app.llm.factory import reset_provider

    preset_id = body.get("preset", "")
    if preset_id not in config.LLM_PRESETS:
        return {"error": f"Unknown preset: {preset_id}. Available: {list(config.LLM_PRESETS.keys())}"}

    preset = config.LLM_PRESETS[preset_id]

    if preset_id == "ollama":
        config.LLM_PROVIDER = "ollama"
        config.ACTIVE_LLM_PRESET = "ollama"
        reset_provider()
        return {"success": True, "preset": preset_id, "provider": "ollama"}

    elif preset_id == "gemma-e2b-litert":
        # Resolve model path: user_config > config > registry recommended
        from app.llm.model_registry import MODEL_REGISTRY, get_model_status
        from app.user_config_manager import get_model_path as get_user_model_path

        model_path = get_user_model_path("gemma-e2b-litert") or config.GEMMA_E2B_LITERT_MODEL_PATH
        if not model_path:
            model_path = MODEL_REGISTRY.get("gemma-e2b-litert", {}).get("recommended_path", "")

        if not model_path or not Path(model_path).exists():
            return {
                "success": False,
                "error": "Gemma E2B model not found",
                "error_code": "model_not_found",
                "message": "Download the model file and set its path.",
                "hint": "Set GEMMA_E2B_LITERT_MODEL_PATH in config.py or use Model Manager to set the path.",
            }

        # Model file exists - check CLI first, then SDK
        from app.llm.litert_cli_provider import find_cli
        cli_ok = bool(find_cli())
        try:
            import litert_lm  # type: ignore
            sdk_ok = True
        except ImportError:
            sdk_ok = False

        if not cli_ok and not sdk_ok:
            return {
                "success": False,
                "error": "LiteRT-LM runtime missing",
                "error_code": "runtime_missing",
                "message": "Model file found, but neither litert-lm CLI nor Python SDK is installed.",
                "model_path": model_path,
                "hint": "Install litert-lm CLI or use Model Manager → Diagnose LiteRT.",
            }

        config.LLM_PROVIDER = "litert"
        config.LITERT_CONFIG["model_path"] = model_path
        config.ACTIVE_LLM_PRESET = "gemma-e2b-litert"
        reset_provider()
        return {"success": True, "preset": preset_id, "provider": "litert", "model_path": model_path}

    elif preset_id == "litert-custom":
        model_path = config.LITERT_CONFIG.get("model_path", "")
        if not model_path or not Path(model_path).exists():
            return {
                "success": False,
                "error": "Custom LiteRT model not found",
                "error_code": "model_not_found",
                "hint": "Set LITERT_CONFIG['model_path'] in config.py",
            }

        try:
            import litert_lm  # type: ignore
            sdk_ok = True
        except ImportError:
            sdk_ok = False

        if not sdk_ok:
            return {
                "success": False,
                "error": "LiteRT-LM SDK missing",
                "error_code": "sdk_missing",
                "message": "Model file found, but LiteRT-LM SDK/runtime is not installed.",
                "model_path": model_path,
            }

        config.LLM_PROVIDER = "litert"
        config.ACTIVE_LLM_PRESET = "litert-custom"
        reset_provider()
        return {"success": True, "preset": preset_id, "provider": "litert", "model_path": model_path}

    return {"error": "Unhandled preset"}


# --- Model Import ---

@app.post("/api/models/import/start")
async def api_import_start(body: dict):
    """Start a model import session."""
    from app.llm.model_import import start_import
    filename = body.get("filename", "")
    size = body.get("size", 0)
    model_name = body.get("model_name", "")
    return start_import(filename, size, model_name)


@app.post("/api/models/import/chunk")
async def api_import_chunk(request: Request):
    """Receive a chunk of model data."""
    from app.llm.model_import import receive_chunk
    form = await request.form()
    import_id = form.get("import_id", "")
    chunk_index = int(form.get("chunk_index", "0"))
    file = form.get("chunk")
    if not file or not import_id:
        return {"success": False, "error": "import_id and chunk are required"}
    data = await file.read()
    return receive_chunk(import_id, chunk_index, data)


@app.post("/api/models/import/finish")
async def api_import_finish(body: dict):
    """Finish import and combine chunks."""
    from app.llm.model_import import finish_import
    import_id = body.get("import_id", "")
    if not import_id:
        return {"error": "import_id is required"}
    return finish_import(import_id)


@app.get("/api/models/import/status/{import_id}")
async def api_import_status(import_id: str):
    """Get import progress."""
    from app.llm.model_import import get_import_status
    return get_import_status(import_id)


@app.delete("/api/models/import/{import_id}")
async def api_import_cancel(import_id: str):
    """Cancel an import."""
    from app.llm.model_import import cancel_import
    return cancel_import(import_id)


# --- Goals ---

@app.post("/api/goals/analyze")
async def api_analyze_goal(body: dict):
    """Analyze a goal and recommend a template."""
    from app.goals.goal_analyzer import analyze_goal
    message = body.get("message", "")
    if not message:
        return {"error": "message is required"}
    analysis = analyze_goal(message)
    return {
        "project_type": analysis.project_type,
        "recommended_template": analysis.recommended_template,
        "variables": analysis.variables,
        "confidence": analysis.confidence,
        "reasoning": analysis.reasoning,
    }


@app.post("/api/goals/run")
async def api_run_goal(body: dict):
    """Run a goal end-to-end (non-streaming, returns final result)."""
    from app.goals.goal_runner import run_goal
    message = body.get("message", "")
    mode = body.get("mode", "safe")
    if not message:
        return {"error": "message is required"}

    result = None
    async for event in run_goal(message, mode):
        result = event  # Keep last event

    return result or {"error": "No result"}


@app.get("/api/goals/{task_id}/status")
async def api_goal_status(task_id: str):
    """Get goal execution status."""
    task = db.get_task(task_id)
    if not task:
        return {"error": "Task not found"}

    from app.workspace.manager import get_task_workspace
    task_ws = get_task_workspace(task_id)
    has_export = (task_ws / "artifacts").exists() and any((task_ws / "artifacts").glob("task-*.zip"))

    return {
        "task_id": task_id,
        "status": task.get("status", "unknown"),
        "message": task.get("message", ""),
        "summary": task.get("summary", ""),
        "export_ready": has_export,
    }


# --- Templates ---

@app.get("/api/templates")
async def api_list_templates(category: str = ""):
    """List available project templates."""
    from app.templates.registry import list_templates
    return {"templates": list_templates(category)}


@app.get("/api/templates/{template_id}")
async def api_get_template(template_id: str):
    """Get template details."""
    from app.templates.registry import get_template
    t = get_template(template_id)
    if not t:
        return {"error": f"Template not found: {template_id}"}
    return {"id": t["id"], "name": t["name"], "description": t["description"],
            "category": t["category"], "variables": t["variables"],
            "file_count": len(t["files"]), "files": list(t["files"].keys())}


@app.post("/api/tasks/{task_id}/templates/{template_id}/generate")
async def api_generate_template(task_id: str, template_id: str, body: dict = {}):
    """Generate project from template."""
    from app.templates.generator import generate_from_template
    variables = body.get("variables", {})
    return generate_from_template(task_id, template_id, variables)


# --- Export ---

@app.post("/api/tasks/{task_id}/export")
async def api_export_task(task_id: str):
    """Create a ZIP export of a task."""
    from app.artifacts.exporter import create_task_export
    return create_task_export(task_id)


@app.get("/api/tasks/{task_id}/export/download")
async def api_download_export(task_id: str):
    """Download the task ZIP export."""
    from fastapi.responses import FileResponse
    from app.workspace.manager import get_task_workspace

    task_ws = get_task_workspace(task_id)
    # Find the zip file
    artifacts_dir = task_ws / "artifacts"
    if not artifacts_dir.exists():
        return {"error": "No export found. Run POST /api/tasks/{task_id}/export first."}

    zips = list(artifacts_dir.glob("task-*.zip"))
    if not zips:
        return {"error": "No export ZIP found."}

    zip_file = sorted(zips, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    return FileResponse(path=str(zip_file), filename=zip_file.name, media_type="application/zip")


@app.get("/api/tasks/{task_id}/export/status")
async def api_export_status(task_id: str):
    """Check if an export exists for a task."""
    from app.workspace.manager import get_task_workspace

    task_ws = get_task_workspace(task_id)
    artifacts_dir = task_ws / "artifacts"
    if not artifacts_dir.exists():
        return {"exists": False}

    zips = list(artifacts_dir.glob("task-*.zip"))
    if not zips:
        return {"exists": False}

    latest = sorted(zips, key=lambda f: f.stat().st_mtime, reverse=True)[0]
    return {
        "exists": True,
        "filename": latest.name,
        "size": latest.stat().st_size,
        "path": str(latest.relative_to(task_ws)),
    }


# --- Models ---

@app.get("/api/models")
async def api_models_list():
    """Get the model registry."""
    from app.llm.model_registry import MODEL_REGISTRY
    return {"models": [{"id": k, **{kk: vv for kk, vv in v.items() if kk != "download_commands"}} for k, v in MODEL_REGISTRY.items()]}


@app.get("/api/models/status")
async def api_models_status():
    """Get status of all registered models."""
    from app.llm.model_registry import get_all_models_status
    from app.user_config_manager import load_user_config
    cfg = load_user_config()
    return {"models": get_all_models_status(cfg.get("model_paths", {}))}


@app.post("/api/models/check-path")
async def api_models_check_path(body: dict):
    """Check if a model file exists at a given path."""
    path = body.get("path", "")
    if not path:
        return {"exists": False, "error": "path is required"}
    from pathlib import Path as P
    p = P(path)
    exists = p.exists() and p.is_file()
    size = p.stat().st_size if exists else 0
    return {"path": path, "exists": exists, "size": size}


@app.post("/api/models/set-path")
async def api_models_set_path(body: dict):
    """Set the path for a model and persist it."""
    model_id = body.get("model_id", "")
    path = body.get("path", "")
    if not model_id or not path:
        return {"error": "model_id and path are required"}
    from app.user_config_manager import set_model_path
    set_model_path(model_id, path)
    return {"success": True, "model_id": model_id, "path": path}


@app.get("/api/models/download-instructions")
async def api_models_download_instructions(model_id: str = "gemma-e2b-litert"):
    """Get download instructions for a model."""
    from app.llm.model_registry import MODEL_REGISTRY
    if model_id not in MODEL_REGISTRY:
        return {"error": f"Unknown model: {model_id}"}
    model = MODEL_REGISTRY[model_id]
    return {
        "model_id": model_id,
        "name": model["name"],
        "commands": model["install_commands"],
        "license_note": model["license_note"],
        "estimated_size": model["estimated_size"],
        "recommended_path": model["recommended_path"],
    }


@app.get("/api/config")
@app.get("/api/settings")
async def api_get_settings():
    """Get all settings."""
    from app.user_config_manager import load_user_config
    return load_user_config()


@app.post("/api/config")
@app.post("/api/settings")
async def api_set_settings(body: dict):
    """Update settings with validation."""
    from app.user_config_manager import update_settings
    success, data, errors = update_settings(body)
    if success:
        return {"success": True, "settings": data}
    return {"success": False, "errors": errors, "settings": data}


@app.post("/api/settings/reset")
async def api_reset_settings():
    """Reset settings to defaults."""
    from app.user_config_manager import reset_settings
    return {"success": True, "settings": reset_settings()}


@app.get("/api/settings/schema")
async def api_settings_schema():
    """Get settings JSON schema for validation."""
    from app.config.settings_schema import get_settings_schema
    return get_settings_schema()


# --- Memory & RAG ---

@app.post("/api/tasks/{task_id}/memory")
async def api_add_memory(task_id: str, body: dict):
    """Store a memory for a task."""
    from app.memory.memory_store import remember
    mem_type = body.get("type", "note")
    content = body.get("content", "")
    metadata = body.get("metadata")
    if not content:
        return {"error": "content is required"}
    return remember(task_id, mem_type, content, metadata)


@app.get("/api/tasks/{task_id}/memory")
async def api_list_memories(task_id: str, type: Optional[str] = None):
    """List memories for a task."""
    from app.memory.memory_store import list_memories
    return {"memories": list_memories(task_id=task_id, memory_type=type)}


@app.post("/api/tasks/{task_id}/index")
async def api_index_files(task_id: str, body: dict = {}):
    """Index files in a task workspace."""
    from app.memory.indexer import index_task_files
    force = body.get("force", False)
    return index_task_files(task_id, force=force)


@app.get("/api/tasks/{task_id}/index")
async def api_get_index(task_id: str):
    """Get file index for a task."""
    from app.memory.memory_store import get_file_index
    return {"index": get_file_index(task_id)}


@app.post("/api/tasks/{task_id}/search")
async def api_search_files(task_id: str, body: dict):
    """Search indexed files."""
    from app.memory.retriever import search_project_files
    query = body.get("query", "")
    if not query:
        return {"error": "query is required"}
    return search_project_files(task_id, query)


@app.post("/api/tasks/{task_id}/context")
async def api_get_context(task_id: str, body: dict):
    """Get relevant context for a query."""
    from app.memory.retriever import get_relevant_context
    query = body.get("query", "")
    limit = body.get("limit", 5)
    if not query:
        return {"error": "query is required"}
    return get_relevant_context(task_id, query, limit)


@app.post("/api/tasks/{task_id}/summarize")
async def api_summarize(task_id: str):
    """Generate project summary."""
    from app.memory.summarizer import summarize_project
    return summarize_project(task_id)


# --- Sandbox ---

@app.get("/api/sandbox/status")
async def api_sandbox_status():
    """Get sandbox status."""
    from config import SANDBOX_ENABLED
    if not SANDBOX_ENABLED:
        return {"enabled": False, "message": "Sandbox is disabled"}
    from app.sandbox.docker_sandbox import get_docker_sandbox
    sandbox = get_docker_sandbox()
    return sandbox.get_global_status()


@app.post("/api/sandbox/reset")
async def api_sandbox_reset():
    """Reset all sandbox containers."""
    from config import SANDBOX_ENABLED
    if not SANDBOX_ENABLED:
        return {"enabled": False, "message": "Sandbox is disabled"}
    from app.sandbox.docker_sandbox import get_docker_sandbox
    sandbox = get_docker_sandbox()
    return sandbox.reset()


@app.get("/api/sandbox/tasks/{task_id}/status")
async def api_sandbox_task_status(task_id: str):
    """Get sandbox status for a specific task."""
    from config import SANDBOX_ENABLED
    if not SANDBOX_ENABLED:
        return {"enabled": False, "message": "Sandbox is disabled"}
    from app.sandbox.docker_sandbox import get_docker_sandbox
    sandbox = get_docker_sandbox()
    return sandbox.get_container_status(task_id)


# --- Browser ---

class BrowserOpenRequest(BaseModel):
    url: str
    task_id: Optional[str] = "default"


class BrowserScreenshotRequest(BaseModel):
    path: str
    task_id: Optional[str] = "default"


@app.post("/api/browser/open")
async def api_browser_open(request: BrowserOpenRequest):
    """Open a URL in the headless browser."""
    manager = get_browser_manager()
    result = await manager.navigate(request.task_id, request.url)
    db.add_browser_log(
        request.task_id, "open_url", url=request.url,
        result=result.get("title", ""), success=result.get("success", False),
    )
    return result


@app.post("/api/browser/screenshot")
async def api_browser_screenshot(request: BrowserScreenshotRequest):
    """Take a screenshot of the current page."""
    import uuid as _uuid
    manager = get_browser_manager()
    result = await manager.screenshot(request.task_id, request.path)
    db.add_browser_log(
        request.task_id, "screenshot",
        url=None, screenshot_path=request.path,
        success=result.get("success", False),
    )
    # Register as artifact
    if result.get("success"):
        artifact_id = str(_uuid.uuid4())[:12]
        filename = request.path.split("/")[-1]
        db.create_artifact(
            artifact_id=artifact_id,
            task_id=request.task_id,
            artifact_type="screenshot",
            name=filename,
            path=request.path,
            mime_type="image/png",
            size=result.get("size", 0),
        )
        result["artifact_id"] = artifact_id
    return result


@app.get("/api/browser/sessions")
async def api_browser_sessions():
    """Get all active browser sessions."""
    manager = get_browser_manager()
    sessions = await manager.get_active_sessions()
    return {"sessions": sessions}


@app.post("/api/browser/close")
async def api_browser_close(body: dict = {}):
    """Close a browser session."""
    task_id = body.get("task_id", "default")
    manager = get_browser_manager()
    result = await manager.close_session(task_id)
    return result


@app.get("/api/browser/logs/{task_id}")
async def api_browser_logs(task_id: str):
    """Get browser logs for a task."""
    logs = db.get_browser_logs(task_id)
    return {"logs": logs}


# --- Artifacts ---

@app.get("/api/tasks/{task_id}/artifacts")
async def get_task_artifacts(task_id: str):
    """Get all artifacts for a task."""
    artifacts = db.list_artifacts(task_id=task_id)
    return {"artifacts": artifacts}


@app.get("/api/artifacts/{artifact_id}")
async def get_artifact_info(artifact_id: str):
    """Get artifact metadata."""
    artifact = db.get_artifact(artifact_id)
    if not artifact:
        return {"error": "Artifact not found"}
    return artifact


@app.get("/api/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    """Download an artifact file."""
    from fastapi.responses import FileResponse
    from app.workspace.manager import get_task_workspace

    artifact = db.get_artifact(artifact_id)
    if not artifact:
        return {"error": "Artifact not found"}

    task_dir = get_task_workspace(artifact["task_id"])
    file_path = task_dir / artifact["path"]

    if not file_path.exists():
        # Try in files subdir
        file_path = task_dir / "files" / artifact["path"]

    if not file_path.exists():
        return {"error": "Artifact file not found on disk"}

    return FileResponse(
        path=str(file_path),
        filename=artifact["name"],
        media_type=artifact.get("mime_type", "application/octet-stream"),
    )


@app.delete("/api/artifacts/{artifact_id}")
async def delete_artifact_endpoint(artifact_id: str):
    """Delete an artifact."""
    artifact = db.get_artifact(artifact_id)
    if not artifact:
        return {"error": "Artifact not found"}
    db.delete_artifact(artifact_id)
    return {"success": True, "id": artifact_id}


# --- WebSocket Agent ---

@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    """WebSocket endpoint for real-time agent communication."""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "task":
                task_id = str(uuid.uuid4())
                task_content = message.get("content", "")
                mode = message.get("mode", "safe")

                # Store connection for this task (for approval flow)
                active_connections[task_id] = websocket

                # Create task in database
                db.create_task(task_id, task_content, mode)
                db.add_message(task_id, "user", task_content)

                # Send task acknowledgment
                await websocket.send_json({
                    "type": "task_started",
                    "task_id": task_id,
                })

                # Create agent with approval callback
                agent = Agent(task_id=task_id, mode=mode)

                async def request_approval(command: str) -> bool:
                    """Request user approval for a command via WebSocket."""
                    approval_id = db.create_approval(task_id, command)
                    event = asyncio.Event()
                    approval_events[approval_id] = event

                    # Send approval request to frontend
                    await websocket.send_json({
                        "type": "approval_request",
                        "task_id": task_id,
                        "approval_id": approval_id,
                        "command": command,
                    })

                    # Wait for user response (timeout 5 minutes)
                    try:
                        await asyncio.wait_for(event.wait(), timeout=300)
                        result = approval_results.get(approval_id, False)
                    except asyncio.TimeoutError:
                        db.resolve_approval(approval_id, approved=False)
                        result = False
                    finally:
                        approval_events.pop(approval_id, None)
                        approval_results.pop(approval_id, None)

                    return result

                agent.request_approval = request_approval

                # Run agent with streaming
                async for event in agent.run(task_content):
                    await websocket.send_json({
                        "type": "agent_event",
                        "task_id": task_id,
                        "event": event,
                    })

                # Mark task complete
                db.update_task_status(task_id, "completed", event.get("content", ""))
                await websocket.send_json({
                    "type": "task_completed",
                    "task_id": task_id,
                })

                # Cleanup
                active_connections.pop(task_id, None)

            elif message.get("type") == "approve":
                approval_id = message.get("approval_id")
                if approval_id:
                    db.resolve_approval(approval_id, approved=True)
                    if approval_id in approval_events:
                        approval_results[approval_id] = True
                        approval_events[approval_id].set()

            elif message.get("type") == "reject":
                approval_id = message.get("approval_id")
                if approval_id:
                    db.resolve_approval(approval_id, approved=False)
                    if approval_id in approval_events:
                        approval_results[approval_id] = False
                        approval_events[approval_id].set()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass
