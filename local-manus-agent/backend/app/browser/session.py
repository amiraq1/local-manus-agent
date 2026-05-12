"""Browser Session Manager - manages Playwright browser sessions per task.

Uses a dedicated background thread with its own event loop to run Playwright,
avoiding conflicts with the main asyncio loop (required on Windows).
"""
import asyncio
import threading
import queue
from typing import Optional
from pathlib import Path
from urllib.parse import urlparse

from config import BROWSER_ALLOW_EXTERNAL_URLS

# Allowed URL patterns
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Dangerous JS patterns
BLOCKED_JS_PATTERNS = [
    "require('fs')",
    "require('child_process')",
    "process.env",
    "process.exit",
    "__dirname",
    "import('fs')",
    "import('child_process')",
]


class _BrowserWorker:
    """Runs Playwright in a dedicated thread to avoid asyncio conflicts."""

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._request_queue: queue.Queue = queue.Queue()
        self._pw = None
        self._browser = None
        self._contexts: dict[str, dict] = {}  # task_id -> {context, page, url, title, screenshot}
        self._running = False

    def start(self):
        """Start the browser worker thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="browser-worker")
        self._thread.start()

    def _run(self):
        """Main loop of the browser worker thread."""
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        while self._running:
            try:
                request = self._request_queue.get(timeout=1.0)
            except queue.Empty:
                continue

            action = request["action"]
            task_id = request.get("task_id", "default")
            result_future = request["future"]

            try:
                result = self._handle_action(action, task_id, request.get("params", {}))
                result_future.set_result(result)
            except Exception as e:
                result_future.set_result({"success": False, "error": str(e)})

        # Cleanup
        self._cleanup()

    def _handle_action(self, action: str, task_id: str, params: dict) -> dict:
        """Handle a browser action in the worker thread."""
        if action == "navigate":
            return self._do_navigate(task_id, params["url"])
        elif action == "get_text":
            return self._do_get_text(task_id)
        elif action == "get_title":
            return self._do_get_title(task_id)
        elif action == "click":
            return self._do_click(task_id, params["selector"])
        elif action == "type":
            return self._do_type(task_id, params["selector"], params["text"])
        elif action == "screenshot":
            return self._do_screenshot(task_id, params["path"])
        elif action == "evaluate":
            return self._do_evaluate(task_id, params["js_code"])
        elif action == "close":
            return self._do_close(task_id)
        elif action == "get_sessions":
            return self._do_get_sessions()
        elif action == "close_all":
            return self._do_close_all()
        else:
            return {"success": False, "error": f"Unknown action: {action}"}

    def _ensure_page(self, task_id: str):
        """Ensure a page exists for the task."""
        if task_id not in self._contexts:
            context = self._browser.new_context(
                viewport={"width": 1280, "height": 720},
                ignore_https_errors=True,
            )
            page = context.new_page()
            self._contexts[task_id] = {
                "context": context,
                "page": page,
                "url": None,
                "title": None,
                "screenshot": None,
            }

    def _do_navigate(self, task_id: str, url: str) -> dict:
        self._ensure_page(task_id)
        ctx = self._contexts[task_id]
        try:
            response = ctx["page"].goto(url, wait_until="domcontentloaded", timeout=15000)
            ctx["url"] = url
            ctx["title"] = ctx["page"].title()
            return {
                "success": True,
                "url": url,
                "title": ctx["title"],
                "status": response.status if response else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _do_get_text(self, task_id: str) -> dict:
        if task_id not in self._contexts or not self._contexts[task_id]["url"]:
            return {"success": False, "error": "No page loaded"}
        ctx = self._contexts[task_id]
        try:
            text = ctx["page"].inner_text("body")
            text = text[:5000] if len(text) > 5000 else text
            return {"success": True, "text": text, "url": ctx["url"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _do_get_title(self, task_id: str) -> dict:
        if task_id not in self._contexts or not self._contexts[task_id]["url"]:
            return {"success": False, "error": "No page loaded"}
        ctx = self._contexts[task_id]
        try:
            title = ctx["page"].title()
            ctx["title"] = title
            return {"success": True, "title": title, "url": ctx["url"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _do_click(self, task_id: str, selector: str) -> dict:
        if task_id not in self._contexts or not self._contexts[task_id]["url"]:
            return {"success": False, "error": "No page loaded"}
        ctx = self._contexts[task_id]
        try:
            ctx["page"].click(selector, timeout=5000)
            return {"success": True, "selector": selector}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    def _do_type(self, task_id: str, selector: str, text: str) -> dict:
        if task_id not in self._contexts or not self._contexts[task_id]["url"]:
            return {"success": False, "error": "No page loaded"}
        ctx = self._contexts[task_id]
        try:
            ctx["page"].fill(selector, text, timeout=5000)
            return {"success": True, "selector": selector, "text": text}
        except Exception as e:
            return {"success": False, "error": str(e), "selector": selector}

    def _do_screenshot(self, task_id: str, path: str) -> dict:
        if task_id not in self._contexts or not self._contexts[task_id]["url"]:
            return {"success": False, "error": "No page loaded"}
        ctx = self._contexts[task_id]
        try:
            from app.workspace.manager import get_task_workspace
            task_dir = get_task_workspace(task_id)
            full_path = task_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            ctx["page"].screenshot(path=str(full_path), full_page=True)
            ctx["screenshot"] = path
            size = full_path.stat().st_size
            return {"success": True, "path": path, "size": size, "url": ctx["url"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _do_evaluate(self, task_id: str, js_code: str) -> dict:
        if task_id not in self._contexts or not self._contexts[task_id]["url"]:
            return {"success": False, "error": "No page loaded"}
        ctx = self._contexts[task_id]
        try:
            result = ctx["page"].evaluate(js_code)
            if result is None:
                result_str = "null"
            elif isinstance(result, (str, int, float, bool)):
                result_str = str(result)
            else:
                import json
                result_str = json.dumps(result, default=str)[:2000]
            return {"success": True, "result": result_str}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _do_close(self, task_id: str) -> dict:
        if task_id in self._contexts:
            ctx = self._contexts[task_id]
            try:
                ctx["page"].close()
                ctx["context"].close()
            except Exception:
                pass
            del self._contexts[task_id]
        return {"success": True, "message": f"Session closed for task {task_id}"}

    def _do_get_sessions(self) -> dict:
        sessions = []
        for task_id, ctx in self._contexts.items():
            sessions.append({
                "task_id": task_id,
                "active": True,
                "url": ctx["url"],
                "title": ctx["title"],
                "last_screenshot": ctx["screenshot"],
            })
        return {"sessions": sessions}

    def _do_close_all(self) -> dict:
        for task_id in list(self._contexts.keys()):
            self._do_close(task_id)
        return {"success": True}

    def _cleanup(self):
        """Cleanup all resources."""
        for task_id in list(self._contexts.keys()):
            self._do_close(task_id)
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        except Exception:
            pass

    def stop(self):
        """Stop the worker thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)

    def execute(self, action: str, task_id: str = "default", **params) -> "asyncio.Future":
        """Submit an action to the worker and return a future."""
        future = asyncio.get_event_loop().create_future()

        # Create a threading event-based bridge
        result_holder = {"value": None, "done": threading.Event()}

        def _bridge_future():
            """Bridge between thread result and asyncio future."""
            result_holder["done"].wait(timeout=30)
            if not future.done():
                future.get_loop().call_soon_threadsafe(
                    future.set_result, result_holder["value"]
                )

        class _ResultFuture:
            def set_result(self, value):
                result_holder["value"] = value
                result_holder["done"].set()

        rf = _ResultFuture()
        self._request_queue.put({
            "action": action,
            "task_id": task_id,
            "params": params,
            "future": rf,
        })

        # Start bridge in background
        bridge_thread = threading.Thread(target=_bridge_future, daemon=True)
        bridge_thread.start()

        return future


# Global worker instance
_worker: Optional[_BrowserWorker] = None


def _get_worker() -> _BrowserWorker:
    """Get or create the browser worker."""
    global _worker
    if _worker is None:
        _worker = _BrowserWorker()
        _worker.start()
        # Give it time to initialize
        import time
        time.sleep(1)
    return _worker


# --- Public async API ---

class BrowserSessionManager:
    """Async interface to the browser worker."""

    async def navigate(self, task_id: str, url: str) -> dict:
        """Navigate to a URL."""
        # Security check first (no need to send to worker)
        safe, reason = is_url_allowed(url)
        if not safe:
            return {"success": False, "error": reason}

        worker = _get_worker()
        return await worker.execute("navigate", task_id, url=url)

    async def get_text(self, task_id: str) -> dict:
        worker = _get_worker()
        return await worker.execute("get_text", task_id)

    async def get_title(self, task_id: str) -> dict:
        worker = _get_worker()
        return await worker.execute("get_title", task_id)

    async def click(self, task_id: str, selector: str) -> dict:
        worker = _get_worker()
        return await worker.execute("click", task_id, selector=selector)

    async def type_text(self, task_id: str, selector: str, text: str) -> dict:
        worker = _get_worker()
        return await worker.execute("type", task_id, selector=selector, text=text)

    async def screenshot(self, task_id: str, path: str) -> dict:
        # Security check
        safe, reason = is_screenshot_path_safe(path)
        if not safe:
            return {"success": False, "error": reason}

        worker = _get_worker()
        return await worker.execute("screenshot", task_id, path=path)

    async def evaluate(self, task_id: str, js_code: str) -> dict:
        # Security check
        safe, reason = is_js_safe(js_code)
        if not safe:
            return {"success": False, "error": reason}

        worker = _get_worker()
        return await worker.execute("evaluate", task_id, js_code=js_code)

    async def close_session(self, task_id: str) -> dict:
        worker = _get_worker()
        return await worker.execute("close", task_id)

    async def close_all(self) -> dict:
        worker = _get_worker()
        return await worker.execute("close_all")

    async def get_active_sessions(self) -> list[dict]:
        worker = _get_worker()
        result = await worker.execute("get_sessions")
        return result.get("sessions", [])


# Global manager instance
_manager: Optional[BrowserSessionManager] = None


def get_browser_manager() -> BrowserSessionManager:
    """Get the global browser session manager."""
    global _manager
    if _manager is None:
        _manager = BrowserSessionManager()
    return _manager


# --- Security helpers ---

def is_url_allowed(url: str) -> tuple[bool, str]:
    """Check if a URL is allowed to be opened."""
    try:
        parsed = urlparse(url)
    except Exception:
        return False, f"Invalid URL: {url}"

    if parsed.scheme not in ("http", "https"):
        return False, f"Only http/https URLs allowed, got: {parsed.scheme}"

    host = parsed.hostname or ""

    if host in ALLOWED_HOSTS:
        return True, "OK"

    if BROWSER_ALLOW_EXTERNAL_URLS:
        return True, "OK"

    return False, f"External URL blocked: {host}. Set BROWSER_ALLOW_EXTERNAL_URLS=true to allow."


def is_screenshot_path_safe(path: str) -> tuple[bool, str]:
    """Check if a screenshot path is safe."""
    if Path(path).is_absolute():
        return False, "Screenshot path must be relative"

    valid_extensions = (".png", ".jpg", ".jpeg", ".webp")
    if not any(path.lower().endswith(ext) for ext in valid_extensions):
        return False, f"Screenshot must have image extension: {valid_extensions}"

    # Block path traversal
    if ".." in path.replace("\\", "/").split("/"):
        return False, "Path traversal not allowed"

    return True, "OK"


def is_js_safe(js_code: str) -> tuple[bool, str]:
    """Check if JavaScript code is safe to execute in browser."""
    code_lower = js_code.lower()

    for pattern in BLOCKED_JS_PATTERNS:
        if pattern.lower() in code_lower:
            return False, f"Blocked JS pattern: {pattern}"

    if "file://" in code_lower:
        return False, "file:// protocol access is blocked"

    return True, "OK"
