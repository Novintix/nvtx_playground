from typing import TypedDict, List, Dict, Optional

class AgentState(TypedDict):
    incident: str
    severity: int
    occurrence: int
    detection: int
    rpn: Optional[int]
    is_rca_required: bool
    candidate_causes: List[str]
    top_cause: Optional[Dict]
    ranked_causes: List[Dict]
    analysis_report: str
    status: str # e.g., "assessment", "mapping", "evidence_check", "5_why", "completed", "error"
