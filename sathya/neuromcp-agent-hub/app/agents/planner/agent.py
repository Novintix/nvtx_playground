from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set, Tuple

from jsonschema import validate as jsonschema_validate
from jsonschema.exceptions import ValidationError

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.config.settings import get_settings
from app.agents.planner.prompt import SYSTEM_PROMPT
from app.agents.planner.schema import Plan


# ===============================
# JSON Extraction Guardrail
# ===============================

def extract_json(text: str) -> Dict[str, Any]:
    """Strictly extract JSON from model output."""
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:
            return json.loads(text[start:end+1])

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
    """Ensure depends_on references earlier steps only."""
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
    """Validate tool name + schema correctness."""
    allowed, tool_map = build_tool_maps(available_tools)

    for step in plan["steps"]:
        tool = step["tool"]

        if tool is None:
            continue

        if tool not in allowed:
            raise ValueError(f"Hallucinated tool: {tool}")

        schema = tool_map[tool]["input_schema"]
        data = step.get("input", {})

        try:
            jsonschema_validate(instance=data, schema=schema)
        except ValidationError as e:
            raise ValueError(f"Tool input schema mismatch: {e.message}")


# ===============================
# Groq LLM Loader
# ===============================

def make_llm() -> ChatOpenAI:
    """Groq LLM configuration (Production Ready)."""
    s = get_settings()
    m = s.model

    return ChatOpenAI(
        model=m.model,
        api_key=s.groq_api_key,
        base_url=m.base_url,

        temperature=m.temperature,
        max_tokens=m.max_tokens,
        timeout=m.timeout_s,

        top_p=m.top_p,
        frequency_penalty=m.frequency_penalty,
        presence_penalty=m.presence_penalty,
    )


# ===============================
# Planner Main Function
# ===============================

def create_plan_with_groq(user_request: str,
                         available_tools: List[Dict[str, Any]],
                         retries: int = 2) -> Plan:
    """
    Generates a tool-valid plan using Groq LLM + strict guardrails.
    """

    llm = make_llm()
    error_msg = None

    for attempt in range(retries + 1):

        prompt = f"""
User Request:
{user_request}

Available Tools:
{json.dumps(available_tools, indent=2)}

Return ONLY JSON plan.
"""

        if error_msg:
            prompt += f"\nPrevious output failed:\n{error_msg}\nFix it."

        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
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
