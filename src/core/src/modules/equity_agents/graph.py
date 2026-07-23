"""
LangGraph StateGraph pipeline for the 10+1 equity research agent system.

Replaces the manual asyncio.gather + ThreadPoolExecutor orchestration.

Graph topology:
  START -> phase1 (6 agents) -> phase2 (3 agents) -> phase3_thesis -> phase3_editor -> END
"""

import asyncio
import json
import logging
import operator
from typing import TypedDict, Dict, List, Annotated

from langgraph.graph import StateGraph, END
from langchain_core.messages import SystemMessage, HumanMessage

from .base import ModuleData, create_llm
from .agent_manager import _AGENT_REGISTRY

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------


class AgentState(TypedDict):
    """Shared state for the LangGraph pipeline.

    ``results`` uses operator.or_ so nodes running in parallel can merge their
    output dicts safely.  ``module_data`` carries the mutable data bus through
    each phase; phase nodes update ``module_results`` in-place for cross-phase
    access.
    """

    module_data: ModuleData
    results: Annotated[Dict[str, dict], operator.or_]


# ---------------------------------------------------------------------------
# Single-agent runner
# ---------------------------------------------------------------------------


async def run_single_agent(
    module_name: str,
    module_data: ModuleData,
    model: str,
    api_key: str,
    base_url: str,
) -> dict:
    """Execute one agent using LangChain ChatOpenAI with manual JSON mode.

    DeepSeek requires the word "json" in the prompt when using
    ``response_format={"type": "json_object"}``.  We inject the Pydantic
    JSON schema into the system prompt and parse the response manually.

    Args:
        module_name: Registry key (e.g. "industry_analysis").
        module_data: The shared data bus (prompt method is called on it).
        model: LLM model name.
        api_key: API key.
        base_url: API base URL.

    Returns:
        Parsed dict matching the agent's Pydantic output schema, or
        ``{"error": ..., "module": ...}`` on failure.
    """
    reg = _AGENT_REGISTRY.get(module_name)
    if not reg:
        return {"error": f"Unknown module: {module_name}"}

    prompt_method = getattr(module_data, reg["prompt_method"], None)
    if not prompt_method:
        return {"error": f"No prompt method for {module_name}"}

    user_prompt = prompt_method()
    output_type = reg["output_type"]
    schema_str = json.dumps(reg["schema"], indent=2)

    # Language directive
    lang_directive = ""
    if module_data.language == "zh":
        lang_directive = (
            "\n\n[LANGUAGE]\n"
            "CRITICAL: All content must be in Chinese (Simplified Chinese / 简体中文). "
            "All field values — including descriptions, summaries, analysis text, "
            "rating labels, and every string output — must be written in Chinese. "
            "Only preserve English for proper nouns (company names, tickers, "
            "product names) and numerical data.\n"
        )

    # DeepSeek requires the word "json" in the prompt for json_object mode
    system_content = (
        f"{reg['instructions']}{lang_directive}\n\n"
        f"OUTPUT FORMAT: Respond with a valid JSON object matching the schema below.\n"
        f"```json\n{schema_str}\n```"
    )

    llm = create_llm(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.25,
        max_tokens=4000,
    )

    try:
        response = await llm.ainvoke(
            [
                SystemMessage(content=system_content),
                HumanMessage(content=user_prompt),
            ]
        )
        content = _clean_json_response(response.content)
        parsed = json.loads(content)
        # Validate and convert to dict via Pydantic
        return output_type.model_validate(parsed).model_dump()
    except Exception as e:
        logger.error(f"Agent '{module_name}' failed: {e}")
        # Retry once with lower temperature
        try:
            llm_retry = create_llm(
                model=model, api_key=api_key, base_url=base_url,
                temperature=0.1, max_tokens=4000,
            )
            retry_system = (
                f"{reg['instructions']}\n\n"
                f"CRITICAL: Respond with ONLY a JSON object. Start with {{, end with }}.\n"
                f"```json\n{schema_str}\n```"
            )
            response = await llm_retry.ainvoke(
                [
                    SystemMessage(content=retry_system),
                    HumanMessage(content=user_prompt),
                ]
            )
            content = _clean_json_response(response.content)
            parsed = json.loads(content)
            return output_type.model_validate(parsed).model_dump()
        except Exception as e2:
            logger.error(f"Agent '{module_name}' retry also failed: {e2}")
            return {"error": str(e), "module": module_name}


def _clean_json_response(content: str) -> str:
    """Strip markdown fences and other LLM artifacts from JSON output."""
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines)
    return content.strip()


# ---------------------------------------------------------------------------
# Phase node factory
# ---------------------------------------------------------------------------


def create_phase_node(
    modules: List[str],
    model: str,
    api_key: str,
    base_url: str,
) -> "callable":
    """Build an async LangGraph node that runs *modules* in parallel.

    After all agents finish, the node merges results into the shared state and
    updates ``module_data.module_results`` so subsequent phases can read prior
    outputs via their ``prompt_*`` methods.
    """

    async def phase_node(state: AgentState) -> dict:
        module_data = state["module_data"]

        tasks = [
            run_single_agent(m, module_data, model, api_key, base_url)
            for m in modules
        ]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        new_results: Dict[str, dict] = {}
        for name, result in zip(modules, gathered):
            if isinstance(result, Exception):
                logger.error(f"Module '{name}' raised: {result}")
                new_results[name] = {"error": str(result)}
            else:
                new_results[name] = result

        # Update module_results for cross-phase access
        if module_data.module_results is None:
            module_data.module_results = {}
        module_data.module_results.update(new_results)

        return {"results": new_results}

    return phase_node


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_agent_graph(
    model: str,
    api_key: str,
    base_url: str,
) -> StateGraph:
    """Build the 3-phase LangGraph.

    Returns an **uncompiled** StateGraph so callers can compile it when needed
    (``graph.compile()``).
    """
    from .agent_manager import PHASE_1_MODULES, PHASE_2_MODULES, PHASE_3_MODULES

    builder = StateGraph(AgentState)

    # Phase 1 — 6 independent modules
    builder.add_node(
        "phase1",
        create_phase_node(PHASE_1_MODULES, model, api_key, base_url),
    )

    # Phase 2 — 3 dependent modules (read Phase 1 results)
    builder.add_node(
        "phase2",
        create_phase_node(PHASE_2_MODULES, model, api_key, base_url),
    )

    # Phase 3 — sequential: investment_thesis first, then editor
    builder.add_node(
        "phase3_thesis",
        create_phase_node(["investment_thesis"], model, api_key, base_url),
    )
    builder.add_node(
        "phase3_editor",
        create_phase_node(["editor"], model, api_key, base_url),
    )

    # Edges
    builder.add_edge("phase1", "phase2")
    builder.add_edge("phase2", "phase3_thesis")
    builder.add_edge("phase3_thesis", "phase3_editor")
    builder.add_edge("phase3_editor", END)

    builder.set_entry_point("phase1")

    return builder
