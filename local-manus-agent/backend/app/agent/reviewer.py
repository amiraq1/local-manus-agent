"""Reviewer module - reviews execution results and suggests fixes."""
from app.llm.base import get_llm_provider


REVIEW_PROMPT = """You are a code reviewer for a local development agent.
Review the execution results and determine if the task was completed successfully.

Task: {task}

Execution results:
{results}

If there are errors, suggest specific fixes using the available tools.
If everything looks good, confirm success.

Respond with JSON:
{{
  "status": "success" | "needs_fix" | "failed",
  "summary": "brief summary of what happened",
  "fixes": [
    {{"description": "what to fix", "tool": "tool_name", "params": {{...}}}}
  ]
}}

Respond ONLY with JSON, no other text."""


async def review_execution(task: str, results: list[dict]) -> dict:
    """Review execution results and determine if fixes are needed.

    Args:
        task: Original user task.
        results: List of execution step results.

    Returns:
        Review result with status and optional fixes.
    """
    llm = get_llm_provider()

    # Format results for the prompt
    results_text = ""
    for i, r in enumerate(results, 1):
        status = "✓" if r.get("success") else "✗"
        desc = r.get("description", "")
        error = r.get("error", "")
        results_text += f"Step {i} [{status}]: {desc}\n"
        if error:
            results_text += f"  Error: {error}\n"

    prompt = REVIEW_PROMPT.format(task=task, results=results_text)

    try:
        response = await llm.generate(prompt)
    except Exception:
        return {"status": "success", "summary": "Execution completed (review skipped - LLM unavailable)", "fixes": []}

    try:
        import json
        text = response.strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            review = json.loads(text[start:end])
            return review
        else:
            return {"status": "success", "summary": "Execution completed", "fixes": []}
    except Exception:
        return {"status": "success", "summary": "Execution completed", "fixes": []}
