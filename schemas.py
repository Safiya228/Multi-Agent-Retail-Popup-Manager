from dataclasses import dataclass
from typing import Any, Dict

SEVERITIES = ("low", "medium", "high", "critical")


@dataclass
class AgentMessage:
    """Standard message every agent publishes to the Supervisor."""

    agent_name: str
    issue_type: str
    severity: str                  # one of SEVERITIES
    recommendation: str
    confidence: float              # 0.0 - 1.0
    requires_human_approval: bool
    evidence: Dict[str, Any]       # raw data supporting the recommendation

    def __post_init__(self):
        if self.severity not in SEVERITIES:
            raise ValueError(f"severity must be one of {SEVERITIES}, got {self.severity!r}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be between 0 and 1, got {self.confidence}")
