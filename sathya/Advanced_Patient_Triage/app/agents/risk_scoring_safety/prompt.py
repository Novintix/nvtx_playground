SYSTEM_PROMPT = """
Risk Scoring & Safety Agent (Deterministic)

This agent is NOT an LLM. It is a config-driven rules engine.

GOAL:
- Convert Agent 2 hypothesis output into a numeric risk_score [0..1]
- Convert score into risk_level: LOW / MEDIUM / HIGH
- Add safety_flags to prevent underestimation

HOW:
- Loads app/config/risk_rules.yaml
- Base score depends on Agent 2 risk_level
- Applies rule boosts based on clinical_notes fields
- Clamps score between 0 and 1
- Converts to risk level using configured thresholds
- Adds final_flags from config for each risk level
"""
