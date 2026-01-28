from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel, Field

class ValidationResult(BaseModel):
    valid: bool = True
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ApprovalRequest(BaseModel):
    step_id: str
    tool: str
    reason: str
    input_preview: Dict[str, Any] = Field(default_factory=dict)
