"""Main FastAPI application for Local Manus Agent."""
import asyncio
import json
import uuid
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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


@app.get("/api/llm/status")
async def api_llm_status():
    """Get LLM provider status."""
    from app.llm.factory import get_provider_status
    return get_provider_status()


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
