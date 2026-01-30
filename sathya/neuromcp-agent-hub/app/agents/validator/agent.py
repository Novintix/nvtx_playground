from __future__ import annotations

from typing import Any, Dict, List, Tuple, Set
from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError

from app.agents.validator.schema import ValidationResult, ApprovalRequest


def _tool_maps(available_tools: List[Dict[str, Any]]) -> Tuple[Set[str], Dict[str, Dict[str, Any]]]:
    allowed = set()
    tool_map: Dict[str, Dict[str, Any]] = {}
    for t in available_tools:
        name = t.get("name")
        if isinstance(name, str) and name:
            allowed.add(name)
            tool_map[name] = t
    return allowed, tool_map


def validate_plan_neurosymbolic(
    plan: Dict[str, Any],
    available_tools: List[Dict[str, Any]],
    default_timezone: str = "Asia/Kolkata",
) -> Tuple[ValidationResult, List[ApprovalRequest], Dict[str, Any]]:
    """
    Returns:
    - validation_result (valid/errors/warnings)
    - pending_approvals (list of steps requiring user approval)
    - patched_plan (may be modified e.g., timezone)
    """
    result = ValidationResult(valid=True)
    pending: List[ApprovalRequest] = []

    if not isinstance(plan, dict) or "steps" not in plan:
        return ValidationResult(valid=False, errors=["Plan missing 'steps'"]), [], plan

    steps = plan.get("steps", [])
    if not isinstance(steps, list) or len(steps) == 0:
        return ValidationResult(valid=False, errors=["Plan has no steps"]), [], plan

    allowed, tool_map = _tool_maps(available_tools)

    # Copy plan so we can patch safely
    patched_plan = {"goal": plan.get("goal", ""), "steps": []}

    # Dependency index check
    ids = []
    for s in steps:
        sid = s.get("id")
        if not isinstance(sid, str):
            result.valid = False
            result.errors.append("Each step must have string 'id'")
        else:
            ids.append(sid)

    id_to_index = {sid: i for i, sid in enumerate(ids)}

    for s in steps:
        sid = s.get("id", "")
        tool = s.get("tool", None)
        step_input = s.get("input", {})

        # 1) Dependency rule: depends_on earlier steps only
        deps = s.get("depends_on", [])
        if not isinstance(deps, list):
            result.valid = False
            result.errors.append(f"{sid}: depends_on must be a list")
        else:
            for d in deps:
                if d not in id_to_index:
                    result.valid = False
                    result.errors.append(f"{sid}: unknown dependency {d}")
                elif id_to_index[d] >= id_to_index.get(sid, 10**9):
                    result.valid = False
                    result.errors.append(f"{sid}: depends_on must reference earlier steps only (bad: {d})")

        # 2) Tool name rule
        if tool is not None:
            if not isinstance(tool, str) or tool not in allowed:
                result.valid = False
                result.errors.append(f"{sid}: invalid tool '{tool}' (hallucination or not allowed)")
        
        # 2.5) Rate limiting check
        if tool is not None and isinstance(tool, str):
            from app.agents.validator.rate_limiter import check_rate_limit
            
            # Check rate limit for this tool
            is_allowed, rate_error = check_rate_limit(tool)
            if not is_allowed:
                result.valid = False
                result.errors.append(f"{sid}: {rate_error}")

        # 3) Input schema rule (symbolic)
        if tool is not None and isinstance(tool, str) and tool in allowed:
            tool_spec = tool_map[tool]
            schema = tool_spec.get("input_schema", {})
            if not isinstance(step_input, dict):
                result.valid = False
                result.errors.append(f"{sid}: input must be an object for tool '{tool}'")
            else:
                try:
                    if isinstance(schema, dict) and schema:
                        jsonschema_validate(instance=step_input, schema=schema)
                except JSONSchemaValidationError as e:
                    result.valid = False
                    result.errors.append(f"{sid}: input schema mismatch for '{tool}': {e.message}")

            # 4) Data Validation Rules (universal checks)
            from app.agents.validator.validation_rules import (
                validate_calendar_event_input,
                validate_slack_message_input
            )
            
            if tool == "calendar.create_event":
                validation_errors = validate_calendar_event_input(step_input)
                if validation_errors:
                    result.valid = False
                    for err in validation_errors:
                        result.errors.append(f"{sid}: {err}")
            
            elif tool == "slack.post_message":
                validation_errors = validate_slack_message_input(step_input)
                if validation_errors:
                    result.valid = False
                    for err in validation_errors:
                        result.errors.append(f"{sid}: {err}")

            # 5) Approval rule (high-risk tools)
            if tool_spec.get("requires_approval", False):
                pending.append(
                    ApprovalRequest(
                        step_id=sid,
                        tool=tool,
                        reason="High-risk tool requires approval",
                        input_preview=step_input,
                    )
                )

            # 6) Policy patch: timezone normalization for calendar tools (optional)
            if tool.startswith("calendar.") and isinstance(step_input, dict):
                tz = step_input.get("timezone")
                if tz and tz != default_timezone:
                    result.warnings.append(
                        f"{sid}: timezone '{tz}' replaced with default '{default_timezone}'"
                    )
                    step_input["timezone"] = default_timezone

        patched_plan["steps"].append({**s, "input": step_input})

    return result, pending, patched_plan
