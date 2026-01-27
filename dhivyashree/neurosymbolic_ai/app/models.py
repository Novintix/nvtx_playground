from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LogEntry(BaseModel):
    timestamp: datetime
    level: str
    service: str
    message: str

class Alert(BaseModel):
    timestamp: datetime
    service: str
    alert_name: str
    severity: str

class AnalysisRequest(BaseModel):
    logs: List[LogEntry]
    alerts: List[Alert]

class RootCause(BaseModel):
    cause: str
    confidence: float
    evidence: List[str]
    actionable_insight: str
