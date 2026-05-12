"""Browser automation tools for the agent.

These tools allow the agent to open pages, read content, take screenshots,
and verify that generated projects work correctly in a real browser.
"""
from typing import Optional

from app.browser.session import get_browser_manager

# Global task_id for the current execution context
_current_task_id: Optional[str] = None


def set_browser_task_id(task_id: str):
    """Set the current task ID for browser operations."""
    global _current_task_id
    _current_task_id = task_id


def get_browser_task_id() -> str:
    """Get the current task ID, defaulting to 'default'."""
    return _current_task_id or "default"


async def browser_open_url(url: str) -> dict:
    """Open a URL in the headless browser.

    Args:
        url: URL to navigate to (localhost only by default).

    Returns:
        Dict with success, url, title, status.
    """
    manager = get_browser_manager()
    return await manager.navigate(get_browser_task_id(), url)


async def browser_get_text() -> dict:
    """Get visible text content of the current page.

    Returns:
        Dict with success and text content.
    """
    manager = get_browser_manager()
    return await manager.get_text(get_browser_task_id())


async def browser_get_title() -> dict:
    """Get the title of the current page.

    Returns:
        Dict with success and title.
    """
    manager = get_browser_manager()
    return await manager.get_title(get_browser_task_id())


async def browser_click(selector: str) -> dict:
    """Click an element on the page.

    Args:
        selector: CSS selector for the element to click.

    Returns:
        Dict with success status.
    """
    manager = get_browser_manager()
    return await manager.click(get_browser_task_id(), selector)


async def browser_type(selector: str, text: str) -> dict:
    """Type text into an input field.

    Args:
        selector: CSS selector for the input element.
        text: Text to type.

    Returns:
        Dict with success status.
    """
    manager = get_browser_manager()
    return await manager.type_text(get_browser_task_id(), selector, text)


async def browser_screenshot(path: str) -> dict:
    """Take a screenshot of the current page.

    Saves to the current task's screenshots directory and registers as artifact.

    Args:
        path: Filename for the screenshot (e.g. "preview.png").

    Returns:
        Dict with success, path, and file size.
    """
    import uuid as _uuid
    from app.workspace.manager import get_current_task_id, get_screenshots_dir
    from app import database as _db

    manager = get_browser_manager()
    task_id = get_browser_task_id()

    # Save to task screenshots dir
    screenshots_dir = get_screenshots_dir(task_id)
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Use just the filename, save in screenshots dir
    filename = path.split("/")[-1] if "/" in path else path
    if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
        filename += ".png"

    full_path = str(screenshots_dir / filename)
    rel_path = f"screenshots/{filename}"

    result = await manager.screenshot(task_id, rel_path)

    if result.get("success"):
        # Register as artifact
        artifact_id = str(_uuid.uuid4())[:12]
        _db.create_artifact(
            artifact_id=artifact_id,
            task_id=task_id,
            artifact_type="screenshot",
            name=filename,
            path=rel_path,
            mime_type="image/png",
            size=result.get("size", 0),
        )
        result["artifact_id"] = artifact_id

    return result


async def browser_evaluate(js_code: str) -> dict:
    """Evaluate JavaScript code on the current page.

    Args:
        js_code: JavaScript code to execute.

    Returns:
        Dict with success and evaluation result.
    """
    manager = get_browser_manager()
    return await manager.evaluate(get_browser_task_id(), js_code)


async def browser_close() -> dict:
    """Close the current browser session.

    Returns:
        Dict with success status.
    """
    manager = get_browser_manager()
    return await manager.close_session(get_browser_task_id())
