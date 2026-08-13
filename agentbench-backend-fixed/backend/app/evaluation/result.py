from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class ExecutionResult:
    success: bool

    output: Optional[str] = None
    error: Optional[str] = None

    execution_time: float = 0.0

    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0

    cost: float = 0.0

    model: Optional[str] = None
    score: float = 0.0

    metadata: Dict[str, Any] = field(default_factory=dict)