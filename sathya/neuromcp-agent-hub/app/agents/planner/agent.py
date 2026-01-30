from __future__ import annotations

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List, Set, Tuple

from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.planner.prompt import SYSTEM_PROMPT
from app.agents.planner.schema import Plan


# ===============================
# Time helpers (IST by default)
# ===============================

DEFAULT_TZ = "Asia/Kolkata"

def now_in_tz(tz: str = DEFAULT_TZ) -> datetime:
    return datetime.now(ZoneInfo(tz))

def today_context(tz: str = DEFAULT_TZ) -> Dict[str, str]:
    """
    Give the LLM a stable "today" anchor.
    """
    dt = now_in_tz(tz)
    return {
        "timezone": tz,
        "today_date": dt.date().isoformat(),          # e.g. 2026-01-29
        "now_iso": dt.isoformat(),                    # e.g. 2026-01-29T12:10:00+05:30
        "weekday": dt.strftime("%A"),                 # e.g. Thursday
    }


# ===============================
# JSON Extraction Guardrail
# ===============================

def extract_json(text: str) -> Dict[str, Any]:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end + 1])
        raise ValueError("Model did not return valid JSON")


# ===============================
# Tool Guardrails
# ===============================

def build_tool_maps(tools: List[Dict[str, Any]]) -> Tuple[Set[str], Dict[str, Dict[str, Any]]]:
    allowed = set()
    tool_map = {}
    for t in tools:
        name = t["name"]
        allowed.add(name)
        tool_map[name] = t
    return allowed, tool_map


def validate_dependencies(plan: Dict[str, Any]):
    steps = plan["steps"]
    ids = [s["id"] for s in steps]
    index = {sid: i for i, sid in enumerate(ids)}

    for step in steps:
        for dep in step.get("depends_on", []):
            if dep not in index:
                raise ValueError(f"Dependency {dep} does not exist")
            if index[dep] >= index[step["id"]]:
                raise ValueError(f"{step['id']} depends on future step {dep}")


def validate_tool_inputs(plan: Dict[str, Any], available_tools: List[Dict[str, Any]]):
    allowed, tool_map = build_tool_maps(available_tools)

    for step in plan["steps"]:
        tool = step.get("tool")
        if tool is None:
            continue

        if tool not in allowed:
            raise ValueError(f"Hallucinated tool: {tool}")

        # Check if input_schema exists
        if "input_schema" not in tool_map[tool]:
            raise ValueError(
                f"Tool '{tool}' is missing 'input_schema' in tool registry. "
                f"Available keys: {list(tool_map[tool].keys())}"
            )
        
        schema = tool_map[tool]["input_schema"]
        data = step.get("input", {})

        try:
            jsonschema_validate(instance=data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Tool '{tool}' input schema mismatch: {e.message}")


# ===============================
# Groq LLM Loader
# ===============================

def get_groq_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY missing in environment/.env")

    return ChatGroq(
        api_key=api_key,
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        temperature=0.2,
        max_tokens=1024,
        # NOTE: top_p warning is okay; it goes into model_kwargs
        top_p=0.9,
    )


# ===============================
# Planner Main Function
# ===============================

def create_plan_with_groq(
    user_request: str,
    available_tools: List[Dict[str, Any]],
    retries: int = 2,
    tz: str = DEFAULT_TZ,
) -> Plan:
    """
    Generates a tool-valid plan using Groq LLM + strict guardrails.
    Anchors the model with today's date/time in the selected timezone.
    """

    llm = get_groq_llm()
    error_msg = None

    ctx = today_context(tz)

    for attempt in range(retries + 1):
        prompt = f"""
TODAY_CONTEXT (authoritative):
- Today is {ctx["weekday"]}, date: {ctx["today_date"]}
- Current time (ISO): {ctx["now_iso"]}
- Use timezone: {ctx["timezone"]}

User Request:
{user_request}

Available Tools (authoritative):
{json.dumps(available_tools, indent=2)}

Rules:
- Return ONLY JSON (no markdown).
- If user says "tomorrow", compute relative to TODAY_CONTEXT.
- All datetimes MUST be ISO 8601 with offset (e.g. 2026-01-30T16:00:00+05:30).
"""

        if error_msg:
            prompt += f"\nPrevious output failed:\n{error_msg}\nFix it and return ONLY JSON."

        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])

        try:
            plan_dict = extract_json(response.content)

            # ✅ Pydantic structure validation
            plan_obj = Plan.model_validate(plan_dict)

            # ✅ Dependency + Tool schema validation
            validate_dependencies(plan_dict)
            validate_tool_inputs(plan_dict, available_tools)

            return plan_obj

        except Exception as e:
            error_msg = str(e)

    raise RuntimeError(f"Planner failed after retries: {error_msg}")
