"""
Agent Manager — orchestrates 10 module agents + editor in 3 phases.

Uses raw openai SDK (Chat Completions, not Responses API) for DeepSeek compatibility.

Phase 1 (parallel): Modules 3, 4, 5, 6, 7, 8 — independent analysis
Phase 2 (dependent): Modules 2, 10, 9 — need Phase 1 outputs
Phase 3 (synthesis): Module 1 + Editor — need all prior outputs
"""

import asyncio
import os
import json
import logging
from typing import Dict, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor

from .base import ModuleData, run_agent, schema_from_pydantic

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
    """Orchestrates all agents in 3 phases."""

    def __init__(self, model: str = None):
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self._executor = ThreadPoolExecutor(max_workers=6)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_all(self, data: ModuleData) -> Dict[str, dict]:
        """Run the full 3-phase pipeline."""
        results: Dict[str, dict] = {}

        # Phase 1 — 6 independent modules in parallel
        logger.info("=== Phase 1: 6 parallel modules ===")
        p1 = await self._run_phase(PHASE_1_MODULES, data)
        results.update(p1)
        data.module_results = results

        # Phase 2 — 3 dependent modules
        logger.info("=== Phase 2: 3 dependent modules ===")
        p2 = await self._run_phase(PHASE_2_MODULES, data)
        results.update(p2)
        data.module_results = results

        # Phase 3 — 2 synthesis modules
        logger.info("=== Phase 3: 2 synthesis modules ===")
        p3 = await self._run_phase(PHASE_3_MODULES, data)
        results.update(p3)

        logger.info(f"=== Complete: {len(results)} modules ===")
        return results

    async def generate_module(self, module_name: str, data: ModuleData) -> dict:
        """Run a single module agent."""
        return await self._run_single(module_name, data)

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

    async def _run_single(self, module_name: str, data: ModuleData) -> dict:
        """Execute one agent and return its parsed output dict."""
        reg = _AGENT_REGISTRY.get(module_name)
        if not reg:
            return {"error": f"Unknown module: {module_name}"}

        # Build the user prompt
        prompt_method = getattr(data, reg["prompt_method"], None)
        if not prompt_method:
            return {"error": f"No prompt method for {module_name}"}
        user_prompt = prompt_method()

        # Run synchronously in thread pool (openai SDK is blocking)
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                self._executor,
                lambda: run_agent(
                    instructions=reg["instructions"],
                    output_schema=reg["schema"],
                    user_prompt=user_prompt,
                    model=self.model,
                    api_key=self.api_key,
                    base_url=self.base_url,
                    temperature=0.25,
                    max_tokens=4000,
                ),
            )
            return result
        except Exception as e:
            logger.error(f"Agent '{module_name}' failed: {e}")
            return {"error": str(e), "module": module_name}

    async def _run_phase(self, modules: List[str], data: ModuleData) -> Dict[str, dict]:
        """Run a list of modules in parallel."""
        tasks = [self._run_single(m, data) for m in modules]
        gathered = await asyncio.gather(*tasks, return_exceptions=True)

        results = {}
        for name, result in zip(modules, gathered):
            if isinstance(result, Exception):
                logger.error(f"Module '{name}' raised: {result}")
                results[name] = {"error": str(result)}
            else:
                results[name] = result
        return results

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
