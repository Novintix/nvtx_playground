from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    id: str = Field(..., pattern=r"^S[1-9]\d*$")
    action: str = Field(..., min_length=3)

    tool: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)

    depends_on: List[str] = Field(default_factory=list)
    expected_output: str = Field(..., min_length=3)


class Plan(BaseModel):
    goal: str = Field(..., min_length=3)
    steps: List[PlanStep] = Field(..., min_length=1, max_length=6)
