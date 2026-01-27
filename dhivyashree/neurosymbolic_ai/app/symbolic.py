from typing import List, Optional
from datetime import timedelta
from app.models import LogEntry, Alert, RootCause

class SymbolicReasoningEngine:
    def __init__(self):
        # Definite rules: (Cause, Effect)
        # In a real system, these might be loaded from a knowledge base
        self.causal_rules = [
            ("Database Connection Failed", "API Error 500"),
            ("High CPU Usage", "Slow Response Time"),
            ("Deployment Started", "Service Restart"),
            ("Deployment Started", "High CPU Usage")
        ]

    def _match_pattern(self, log_message: str, pattern_key: str) -> bool:
        """Simple keyword matching to map log text to symbolic concepts."""
        keywords = {
            "Database Connection Failed": ["db", "database", "connection refused", "timeout", "connection reset"],
            "API Error 500": ["500", "internal server error", "api failure", "upstream connect error"],
            "High CPU Usage": ["cpu", "load", "utilization", "high usage", "spike"],
            "Slow Response Time": ["latency", "slow", "timeout", "timed out", "lag"],
            "Deployment Started": ["deploy", "upgrade", "version", "rolling update", "release"],
            "Service Restart": ["restart", "boot", "init", "startup", "reboot"]
        }
        if pattern_key not in keywords:
            return False
            
        return any(k in log_message.lower() for k in keywords[pattern_key])

    def find_root_cause(self, logs: List[LogEntry], alerts: List[Alert]) -> Optional[RootCause]:
        sorted_logs = sorted(logs, key=lambda x: x.timestamp)
        
        # 1. Check for correlated events based on rules
        for i, cause_log in enumerate(sorted_logs):
            for j in range(i + 1, len(sorted_logs)):
                effect_log = sorted_logs[j]
                
                # Check time window (e.g., effect within 5 minutes of cause)
                time_diff = effect_log.timestamp - cause_log.timestamp
                if time_diff > timedelta(minutes=10):
                    break # Too far apart

                # Apply Causal Rules
                for cause_concept, effect_concept in self.causal_rules:
                    if (self._match_pattern(cause_log.message, cause_concept) and 
                        self._match_pattern(effect_log.message, effect_concept)):
                        
                        return RootCause(
                            cause=cause_concept,
                            confidence=0.9, # High confidence because it matches a known rule
                            evidence=[
                                f"Log (Cause): {cause_log.timestamp} - {cause_log.message}",
                                f"Log (Effect): {effect_log.timestamp} - {effect_log.message}",
                                f"Rule Applied: {cause_concept} -> {effect_concept}"
                            ],
                            actionable_insight=f"Investigate {cause_concept}. A known pattern triggered {effect_concept}."
                        )

        # 2. Heuristic: If we have alerts, the earliest critical alert is often the trigger
        critical_alerts = sorted([a for a in alerts if a.severity == "CRITICAL"], key=lambda x: x.timestamp)
        if critical_alerts:
            root_alert = critical_alerts[0]
            return RootCause(
                cause=f"Alert: {root_alert.alert_name}",
                confidence=0.7,
                evidence=[f"First critical alert at {root_alert.timestamp}"],
                actionable_insight=f"Check service {root_alert.service} immediately."
            )

        return None
