from typing import TypedDict, List, Dict, Optional

class DiscoveryState(TypedDict):
    # Standardized Complaint Data
    complaint_data: Dict
    lot_number: str
    
    # Risk Assessment (harmonized with Production)
    severity: int
    occurrence: int
    detection: int
    rpn: Optional[int]
    is_rca_required: bool
    
    # Reasoning Buffers
    physical_attributes: List[str]
    hypotheses: List[Dict] 
    verified_evidence: List[Dict] 
    
    # Results
    analysis_report: str
    status: str 
