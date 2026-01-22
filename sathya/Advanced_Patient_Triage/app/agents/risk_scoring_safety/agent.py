from __future__ import annotations

from typing import Any, Dict, List
from pathlib import Path
import yaml

ROOT_DIR = Path(__file__).resolve().parents[2]  # -> app/
RULES_PATH = ROOT_DIR / "config" / "risk_rules.yaml"


def _normalize(v: Any) -> str:
    return str(v).strip().lower()


def _to_float(v: Any) -> float | None:
    try:
        return float(str(v).strip())
    except Exception:
        return None


def _compare(actual: Any, op: str, expected: Any) -> bool:
    op = _normalize(op)

    if op in ("gte", "lte", "gt", "lt"):
        a = _to_float(actual)
        b = _to_float(expected)
        if a is None or b is None:
            return False
        if op == "gte":
            return a >= b
        if op == "lte":
            return a <= b
        if op == "gt":
            return a > b
        if op == "lt":
            return a < b

    if op == "contains":
        return _normalize(expected) in _normalize(actual)

    a = _normalize(actual)
    b = _normalize(expected)

    if op == "eq":
        # treat yes/true/1 as truthy matches
        if b in ("yes", "true", "1"):
            return a in ("yes", "true", "1")
        return a == b

    if op == "neq":
        return a != b

    return False


def _eval_condition(condition: Dict[str, Any], data: Dict[str, Any]) -> bool:
    if "all" in condition:
        return all(_compare(data.get(c["key"]), c["op"], c["value"]) for c in condition["all"])
    if "any" in condition:
        return any(_compare(data.get(c["key"]), c["op"], c["value"]) for c in condition["any"])
    return False


def load_rules() -> Dict[str, Any]:
    if not RULES_PATH.exists():
        raise FileNotFoundError(f"Risk rules not found: {RULES_PATH}")
    with open(RULES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def risk_scoring_safety_agent(
    risk_output: Dict[str, Any],
    clinical_notes: Dict[str, Any],
) -> Dict[str, Any]:
    cfg = load_rules()

    base_map = cfg.get("base_score_by_risk_level", {})
    thresholds = cfg.get("thresholds", {})
    rules = cfg.get("rules", [])
    final_flags_cfg = cfg.get("final_flags", {})

    # Base score comes from Agent 2 risk_level
    agent2_level = _normalize(risk_output.get("risk_level", "medium"))
    score = float(base_map.get(agent2_level, 0.55))

    safety_flags: List[str] = []

    # Apply rules dynamically from YAML
    for rule in rules:
        cond = rule.get("when", {})
        if _eval_condition(cond, clinical_notes):
            score += float(rule.get("add_score", 0.0))
            safety_flags.extend(rule.get("add_flags", []))

    # Clamp
    score = max(0.0, min(1.0, score))

    # Convert score -> risk level using YAML thresholds
    high_th = float(thresholds.get("HIGH", 0.85))
    med_th = float(thresholds.get("MEDIUM", 0.60))

    if score >= high_th:
        computed_level = "HIGH"
    elif score >= med_th:
        computed_level = "MEDIUM"
    else:
        computed_level = "LOW"

    # ✅ SAFETY: never downgrade below Agent 2
    # Map agent2 risk -> minimum allowed output level
    # (Agent3 only outputs LOW/MEDIUM/HIGH)
    agent2_min = {
        "low": "LOW",
        "medium": "MEDIUM",
        "high": "HIGH",
        "critical": "HIGH",
    }.get(agent2_level, "MEDIUM")

    rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    risk_level = computed_level
    if rank.get(risk_level, 1) < rank.get(agent2_min, 1):
        risk_level = agent2_min
        safety_flags.append("no_downgrade_override")

    # Add final flags from YAML
    safety_flags.extend(final_flags_cfg.get(risk_level, []))

    # Dedupe flags (keep order)
    safety_flags = list(dict.fromkeys(safety_flags))

    return {
        "risk_score": round(score, 2),
        "risk_level": risk_level,
        "safety_flags": safety_flags,
    }
