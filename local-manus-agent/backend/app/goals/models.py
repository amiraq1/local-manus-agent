"""Goal Mode data models."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class GoalAnalysis:
    """Result of analyzing a user goal."""
    original_message: str
    project_type: str  # web, backend, tool, docs
    recommended_template: str
    variables: dict = field(default_factory=dict)
    confidence: float = 0.0
    reasoning: str = ""


@dataclass
class GoalStatus:
    """Status of a running goal."""
    task_id: str
    phase: str  # analyzing, generating, reviewing, previewing, exporting, completed, failed
    progress: int = 0  # 0-100
    template_id: Optional[str] = None
    files_generated: int = 0
    export_ready: bool = False
    preview_url: Optional[str] = None
    error: Optional[str] = None
