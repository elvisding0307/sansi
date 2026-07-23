"""
Agent Manager — orchestrates 10 module agents + editor in 3 phases.

Uses LangGraph (langgraph) for the 3-phase pipeline and langchain-openai
(ChatOpenAI) for LLM calls.  The public API (create_manager, generate_all_sync,
generate_module_sync) is unchanged for backward compatibility.

Phase 1 (parallel): Modules 3, 4, 5, 6, 7, 8 — independent analysis
Phase 2 (dependent): Modules 2, 10, 9 — need Phase 1 outputs
Phase 3 (synthesis): Module 1 + Editor — need all prior outputs
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional

from .base import ModuleData, schema_from_pydantic

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent registry — maps module name → (instructions, output_type, prompt_method)
# ---------------------------------------------------------------------------

_AGENT_REGISTRY = {}

def _register(name: str, instructions: str, output_type: type):
    _AGENT_REGISTRY[name] = {
        "instructions": instructions,
        "output_type": output_type,
        "schema": schema_from_pydantic(output_type),
        "prompt_method": f"prompt_{name}",
    }

# Import and register all agents
from .industry_analysis import INDUSTRY_ANALYSIS_INSTRUCTIONS, IndustryAnalysisOutput
from .company_analysis import COMPANY_ANALYSIS_INSTRUCTIONS, CompanyAnalysisOutput
from .financial_analysis import FINANCIAL_ANALYSIS_INSTRUCTIONS, FinancialAnalysisOutput
from .earnings_forecast import EARNINGS_FORECAST_INSTRUCTIONS, EarningsForecastOutput
from .valuation_analysis import VALUATION_ANALYSIS_INSTRUCTIONS, ValuationAnalysisOutput
from .technical_analysis import TECHNICAL_ANALYSIS_INSTRUCTIONS, TechnicalAnalysisOutput
from .investment_rationale import INVESTMENT_RATIONALE_INSTRUCTIONS, InvestmentRationaleOutput
from .risk_disclosure import RISK_DISCLOSURE_INSTRUCTIONS, RiskDisclosureOutput
from .monitor_signals import MONITOR_SIGNALS_INSTRUCTIONS, MonitorSignalsOutput
from .investment_thesis import INVESTMENT_THESIS_INSTRUCTIONS, InvestmentThesisOutput
from .editor import EDITOR_INSTRUCTIONS, EditorOutput

_register("industry_analysis", INDUSTRY_ANALYSIS_INSTRUCTIONS, IndustryAnalysisOutput)
_register("company_analysis", COMPANY_ANALYSIS_INSTRUCTIONS, CompanyAnalysisOutput)
_register("financial_analysis", FINANCIAL_ANALYSIS_INSTRUCTIONS, FinancialAnalysisOutput)
_register("earnings_forecast", EARNINGS_FORECAST_INSTRUCTIONS, EarningsForecastOutput)
_register("valuation_analysis", VALUATION_ANALYSIS_INSTRUCTIONS, ValuationAnalysisOutput)
_register("technical_analysis", TECHNICAL_ANALYSIS_INSTRUCTIONS, TechnicalAnalysisOutput)
_register("investment_rationale", INVESTMENT_RATIONALE_INSTRUCTIONS, InvestmentRationaleOutput)
_register("risk_disclosure", RISK_DISCLOSURE_INSTRUCTIONS, RiskDisclosureOutput)
_register("monitor_signals", MONITOR_SIGNALS_INSTRUCTIONS, MonitorSignalsOutput)
_register("investment_thesis", INVESTMENT_THESIS_INSTRUCTIONS, InvestmentThesisOutput)
_register("editor", EDITOR_INSTRUCTIONS, EditorOutput)

# ---------------------------------------------------------------------------
# Execution phases
# ---------------------------------------------------------------------------

PHASE_1_MODULES = [
    "industry_analysis",
    "company_analysis",
    "financial_analysis",
    "earnings_forecast",
    "valuation_analysis",
    "technical_analysis",
]

PHASE_2_MODULES = [
    "investment_rationale",
    "risk_disclosure",
    "monitor_signals",
]

PHASE_3_MODULES = [
    "investment_thesis",
    "editor",
]

# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class EquityResearchAgentManager:
    """Orchestrates all agents in 3 phases using LangGraph."""

    def __init__(self, model: str = None):
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self._graph = None  # lazily built & compiled

    def _get_graph(self):
        """Lazy-build and compile the LangGraph app."""
        if self._graph is None:
            from .graph import build_agent_graph

            self._graph = build_agent_graph(
                self.model, self.api_key, self.base_url
            ).compile()
        return self._graph

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_all(self, data: ModuleData) -> Dict[str, dict]:
        """Run the full 3-phase pipeline via LangGraph."""
        app = self._get_graph()

        initial_state = {
            "module_data": data,
            "results": {},
        }

        logger.info("Running LangGraph agent pipeline...")
        final_state = await app.ainvoke(initial_state)
        logger.info(f"LangGraph pipeline complete: {len(final_state['results'])} modules")

        return final_state["results"]

    async def generate_module(self, module_name: str, data: ModuleData) -> dict:
        """Run a single module agent via LangChain."""
        from .graph import run_single_agent

        return await run_single_agent(
            module_name, data, self.model, self.api_key, self.base_url
        )

    def generate_all_sync(self, data: ModuleData) -> Dict[str, dict]:
        """Synchronous wrapper."""
        return asyncio.get_event_loop().run_until_complete(self.generate_all(data))

    def generate_module_sync(self, module_name: str, data: ModuleData) -> dict:
        """Synchronous wrapper for single module."""
        return asyncio.get_event_loop().run_until_complete(
            self.generate_module(module_name, data)
        )

    # ------------------------------------------------------------------
    # Legacy backward-compatible API
    # ------------------------------------------------------------------

    async def generate_text_section(
        self, data: dict, text_type: str, company_name: str, company_ticker: str
    ) -> str:
        """Legacy API — simple text generation for old callers."""
        from openai import OpenAI

        # Map old text types to a simple system prompt
        prompts = {
            "tagline": "Write a 3-sentence professional tagline for an equity research report.",
            "company_overview": "Write a 300-400 word company overview for an equity research report.",
            "investment_overview": "Write a 200-300 word investment overview.",
            "valuation_overview": "Write a 200-300 word valuation analysis.",
            "risks": "List 5 key investment risks in bullet points.",
            "competitor_analysis": "Write a 200-300 word competitor analysis.",
            "major_takeaways": "Provide 4 major takeaways covering Revenue Growth, Gross Profit Margin, SG&A Margin, and EBITDA Margin.",
            "news_summary": "Summarize recent company news in 200-300 words.",
        }

        system_prompt = prompts.get(text_type, f"Provide {text_type} analysis.")
        prompt = self._prepare_legacy_prompt(data, company_name, company_ticker)

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _prepare_legacy_prompt(self, data: dict, company_name: str, company_ticker: str) -> str:
        """Build prompt for legacy simple agents."""
        import pandas as pd

        prompt = f"Company: {company_name} ({company_ticker})\n\n"

        fm = data.get("financial_metrics")
        if fm is not None and not (isinstance(fm, pd.DataFrame) and fm.empty):
            try:
                prompt += f"## Financial Metrics\n{fm.to_markdown()}\n\n"
            except Exception:
                prompt += f"## Financial Metrics\n{str(fm)[:2000]}\n\n"

        for key, label in [("peer_ebitda", "Peer EBITDA"), ("peer_ev_ebitda", "Peer EV/EBITDA")]:
            d = data.get(key)
            if d is not None and not (isinstance(d, pd.DataFrame) and d.empty):
                try:
                    prompt += f"## {label}\n{d.to_markdown()}\n\n"
                except Exception:
                    prompt += f"## {label}\n{str(d)[:1000]}\n\n"

        news = data.get("company_news")
        if news and isinstance(news, list) and len(news) > 0:
            prompt += f"## Recent News ({len(news)} articles)\n"
            for a in news[:10]:
                prompt += f"- {a.get('title', 'N/A')} ({str(a.get('publishedDate', ''))[:10]})\n"
                text = a.get('text', '')
                if text:
                    prompt += f"  {str(text)[:200]}...\n\n"

        return prompt


# ------------------------------------------------------------------
# Factory
# ------------------------------------------------------------------

def create_manager(model: str = None) -> EquityResearchAgentManager:
    """Create an agent manager instance."""
    return EquityResearchAgentManager(model=model)
