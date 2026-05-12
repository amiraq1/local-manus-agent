"""Goal Analyzer - detects project type and recommends templates from user messages."""
import re
from app.goals.models import GoalAnalysis

# Keyword patterns for project type detection
_PATTERNS = {
    "html-landing-page": {
        "keywords": ["landing page", "homepage", "single page", "one page", "portfolio", "product page", "store page", "shop page"],
        "type": "web",
        "confidence": 0.9,
    },
    "nextjs-dashboard": {
        "keywords": ["dashboard", "admin panel", "admin page", "management panel", "analytics"],
        "type": "web",
        "confidence": 0.85,
    },
    "react-vite-app": {
        "keywords": ["react app", "web app", "spa", "single page app", "interactive app", "frontend app"],
        "type": "web",
        "confidence": 0.8,
    },
    "fastapi-api": {
        "keywords": ["api", "rest api", "backend", "server", "microservice", "endpoint"],
        "type": "backend",
        "confidence": 0.9,
    },
    "python-cli-tool": {
        "keywords": ["cli", "command line", "terminal tool", "script", "automation"],
        "type": "tool",
        "confidence": 0.85,
    },
    "docs-site": {
        "keywords": ["documentation", "docs", "wiki", "guide", "manual", "help page"],
        "type": "docs",
        "confidence": 0.85,
    },
}

# Color keywords
_COLORS = {
    "red": "#dc2626", "blue": "#2563eb", "green": "#16a34a", "purple": "#7c3aed",
    "orange": "#ea580c", "pink": "#db2777", "yellow": "#ca8a04", "brown": "#8b4513",
    "warm": "#8b4513", "cool": "#2563eb", "dark": "#1e293b", "teal": "#0d9488",
    "indigo": "#4f46e5", "gold": "#b8860b", "navy": "#1e3a5f",
}


def analyze_goal(message: str) -> GoalAnalysis:
    """Analyze a user goal message and recommend a template.

    Args:
        message: User's goal description.

    Returns:
        GoalAnalysis with recommended template and extracted variables.
    """
    msg_lower = message.lower()

    # Detect project type and template
    best_template = "html-landing-page"  # default
    best_confidence = 0.0
    best_type = "web"

    for template_id, pattern in _PATTERNS.items():
        for keyword in pattern["keywords"]:
            if keyword in msg_lower:
                if pattern["confidence"] > best_confidence:
                    best_template = template_id
                    best_confidence = pattern["confidence"]
                    best_type = pattern["type"]
                    break

    # Extract variables
    variables = extract_variables(message)

    reasoning = f"Detected '{best_type}' project from keywords. Template: {best_template}."
    if variables.get("project_name"):
        reasoning += f" Project name: {variables['project_name']}."

    return GoalAnalysis(
        original_message=message,
        project_type=best_type,
        recommended_template=best_template,
        variables=variables,
        confidence=best_confidence,
        reasoning=reasoning,
    )


def detect_project_type(message: str) -> str:
    """Detect the project type from a message."""
    analysis = analyze_goal(message)
    return analysis.project_type


def recommend_template(message: str) -> str:
    """Recommend a template ID for a message."""
    analysis = analyze_goal(message)
    return analysis.recommended_template


def extract_variables(message: str) -> dict:
    """Extract template variables from a goal message."""
    variables = {}
    msg_lower = message.lower()

    # Extract project name: look for "for X" or "called X" patterns
    name_patterns = [
        r"(?:for|called|named)\s+[\"']?([A-Z][A-Za-z0-9\s&']+?)(?:[\"']?\s*(?:with|using|in|that|$))",
        r"(?:for|called|named)\s+([A-Z][A-Za-z0-9\s&']{2,30})",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, message)
        if match:
            variables["project_name"] = match.group(1).strip().rstrip(".")
            break

    if "project_name" not in variables:
        # Try to extract from "Build a X" pattern
        match = re.search(r"(?:build|create|make)\s+(?:a|an)\s+(.+?)(?:\s+(?:for|with|using|that)|$)", message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) < 40:
                variables["project_name"] = name.title()

    if "project_name" not in variables:
        variables["project_name"] = "My Project"

    # Extract color
    variables["primary_color"] = "#6366f1"  # default
    for color_name, color_hex in _COLORS.items():
        if color_name in msg_lower:
            variables["primary_color"] = color_hex
            break

    # Extract description from the message itself
    variables["description"] = message[:100] if len(message) > 10 else ""

    return variables
