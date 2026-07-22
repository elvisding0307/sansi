"""
Agent infrastructure: ModuleData, agent runner, and prompt helpers.

Uses the raw openai SDK (Chat Completions API) for DeepSeek compatibility.
The openai-agents SDK is NOT used because it requires OpenAI's /v1/responses endpoint
which DeepSeek does not support.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data bus
# ---------------------------------------------------------------------------

@dataclass
class ModuleData:
    """All data available to agents. Each agent only sees its own slice."""

    company_name: str
    company_ticker: str

    # Basic identifiers
    sector: str = ""
    industry: str = ""
    current_price: float = 0.0
    market_cap: float = 0.0  # billions

    # Financial data (dict-based, from DataFrames)
    financial_metrics: Optional[Dict] = None       # historical metrics table
    forecast_data: Optional[Dict] = None            # forecast assumptions & projections
    balance_sheet: Optional[Dict] = None
    cash_flow: Optional[Dict] = None
    income_statement: Optional[Dict] = None

    # Valuation
    valuation_results: Optional[Dict] = None

    # Industry
    industry_data: Optional[Dict] = None

    # Company
    company_profile: Optional[Dict] = None
    business_segments: Optional[List[Dict]] = None
    management: Optional[List[Dict]] = None
    company_history: Optional[List[Dict]] = None

    # Technical
    technical_indicators: Optional[Dict] = None

    # Risk & catalyst
    risk_data: Optional[Dict] = None
    catalyst_data: Optional[Dict] = None

    # News & sentiment
    news_data: Optional[List[Dict]] = None
    sentiment_data: Optional[Dict] = None

    # Peer
    peer_ebitda: Optional[Dict] = None
    peer_ev_ebitda: Optional[Dict] = None
    peer_metrics: Optional[Dict] = None

    # After each phase, store module results here for cross-module access
    module_results: Optional[Dict[str, dict]] = None

    # Language preference
    language: str = "en"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cn(self, en: str, zh: str) -> str:
        return zh if self.language == "zh" else en

    def _fmt_num(self, v: Any, unit: str = "") -> str:
        if v is None:
            return "N/A"
        try:
            n = float(v)
            if abs(n) >= 1e9:
                return f"{n/1e9:.2f}B{unit}"
            if abs(n) >= 1e6:
                return f"{n/1e6:.1f}M{unit}"
            return f"{n:,.1f}{unit}"
        except (ValueError, TypeError):
            return str(v)

    def _fmt_pct(self, v: Any) -> str:
        if v is None:
            return "N/A"
        try:
            return f"{float(v)*100:.1f}%" if abs(float(v)) < 10 else f"{float(v):.1f}%"
        except (ValueError, TypeError):
            return str(v)

    def _dict_to_table(self, d: dict, rows: list[str]) -> str:
        """Render selected rows from a dict-of-lists as a markdown table."""
        if not d or "metrics" not in d:
            return "(No data available)"
        years = [k for k in d if k != "metrics"]
        if not years:
            return str(d)
        # Try to sort years chronologically
        years_sorted = sorted(years, key=lambda y: (y[-1], y[:-1]) if y[-1] in 'AE' else (y, ''))
        metrics_list = d["metrics"]
        header = "| Metric | " + " | ".join(years_sorted) + " |\n"
        sep = "|---" * (len(years_sorted) + 1) + "|\n"
        body = ""
        for metric in rows:
            if metric not in metrics_list:
                continue
            idx = metrics_list.index(metric)
            vals = [str(d[y][idx]) if idx < len(d.get(y, [])) else "N/A" for y in years_sorted]
            body += f"| {metric} | " + " | ".join(vals) + " |\n"
        return header + sep + body

    # ------------------------------------------------------------------
    # Prompt builders — each returns the full user prompt for one agent
    # ------------------------------------------------------------------

    def prompt_industry_analysis(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})",
             f"Sector: {self.sector}  |  Industry: {self.industry}", ""]
        if self.industry_data:
            d = self.industry_data
            p.append("## Industry Data")
            p.append(f"Industry: {d.get('industry_name', self.industry)}")
            p.append(f"Global Market Size: {d.get('market_size', 'N/A')}")
            p.append(f"Historical CAGR: {d.get('historical_cagr', 'N/A')}")
            p.append(f"Forecast CAGR: {d.get('forecast_cagr', 'N/A')}")
            p.append(f"Lifecycle Stage: {d.get('lifecycle_stage', 'N/A')}")
            p.append(f"CR3: {d.get('cr3', 'N/A')}  |  CR5: {d.get('cr5', 'N/A')}")
            trends = d.get('key_trends', [])
            if trends:
                p.append("Key Trends:")
                for t in trends:
                    p.append(f"  - {t}")
        if self.company_profile:
            cp = self.company_profile
            p.append(f"\n## Company Position")
            rev = cp.get('revenue') or cp.get('total_revenue')
            p.append(f"Revenue: {self._fmt_num(rev)}")
            p.append(f"Market Cap: ${self.market_cap:.1f}B" if self.market_cap else "Market Cap: N/A")
            emp = cp.get('employees') or cp.get('fullTimeEmployees')
            p.append(f"Employees: {emp or 'N/A'}")
        if self.peer_metrics:
            p.append(f"\n## Peer Comparison Data")
            p.append(json.dumps(self.peer_metrics, indent=2, default=str))
        return "\n".join(p)

    def prompt_company_analysis(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})",
             f"Sector: {self.sector}  |  Industry: {self.industry}", ""]
        if self.company_profile:
            cp = self.company_profile
            p.append("## Company Profile")
            desc = cp.get('description') or cp.get('business_summary') or cp.get('companyDescription', '')
            if desc:
                p.append(f"Description: {str(desc)[:2000]}")
            p.append(f"CEO: {cp.get('ceo') or cp.get('ceoName', 'N/A')}")
            p.append(f"Founded/IPO: {cp.get('founded') or cp.get('ipoDate', 'N/A')}")
            p.append(f"Exchange: {cp.get('exchange') or cp.get('exchangeShortName', 'N/A')}")
            p.append(f"Website: {cp.get('website', 'N/A')}")
            p.append(f"Employees: {cp.get('fullTimeEmployees', 'N/A')}")
        if self.management:
            p.append("\n## Management Team")
            for m in self.management[:6]:
                p.append(f"- {m.get('name','?')}: {m.get('title','?')}, tenure since {m.get('since','?')}")
                bg = m.get('background','')
                if bg:
                    p.append(f"  Background: {bg}")
        if self.business_segments:
            p.append("\n## Business Segments")
            for seg in self.business_segments:
                rev = self._fmt_num(seg.get('revenue'))
                share = self._fmt_pct(seg.get('share'))
                growth = self._fmt_pct(seg.get('growth'))
                driver = seg.get('key_driver', '')
                p.append(f"- {seg.get('name','?')}: Revenue={rev}, Share={share}, "
                         f"Growth={growth}, Driver: {driver}")
        if self.company_history:
            p.append("\n## Key Milestones")
            for h in self.company_history[:8]:
                p.append(f"- {h.get('year','?')}: {h.get('event','?')}")
        return "\n".join(p)

    def prompt_financial_analysis(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})", ""]
        if self.financial_metrics:
            p.append("## Historical Financial Metrics")
            key_rows = ['Revenue', 'Revenue Growth', 'Gross Profit', 'EBITDA',
                        'EBITDA Margin', 'Net Income', 'EPS', 'ROE', 'ROA',
                        'Free Cash Flow', 'Total Assets', 'Total Liabilities', 'Total Equity']
            p.append(self._dict_to_table(self.financial_metrics, key_rows))
        if self.balance_sheet:
            p.append("\n## Balance Sheet Data (Latest)")
            p.append(json.dumps(self.balance_sheet, default=str)[:1500])
        if self.cash_flow:
            p.append("\n## Cash Flow Data (Latest)")
            p.append(json.dumps(self.cash_flow, default=str)[:1500])
        return "\n".join(p)

    def prompt_earnings_forecast(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})", ""]
        if self.forecast_data:
            p.append("## Forecast Assumptions & Projections")
            p.append(json.dumps(self.forecast_data, indent=2, default=str))
        if self.financial_metrics:
            p.append("\n## Historical Data (for grounding)")
            key_rows = ['Revenue', 'Revenue Growth', 'Contribution Margin',
                        'SG&A Margin', 'EBITDA Margin', 'EPS']
            p.append(self._dict_to_table(self.financial_metrics, key_rows))
        if self.industry_data:
            p.append(f"\n## Industry Context")
            p.append(f"Industry Growth: {self.industry_data.get('forecast_cagr', 'N/A')}")
        return "\n".join(p)

    def prompt_valuation_analysis(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})",
             f"Current Price: ${self.current_price:.2f}" if self.current_price else "Current Price: N/A", ""]
        if self.valuation_results:
            p.append("## Valuation Engine Results")
            p.append(json.dumps(self.valuation_results, indent=2, default=str))
        if self.peer_ev_ebitda:
            p.append("\n## Peer EV/EBITDA Data")
            p.append(json.dumps(self.peer_ev_ebitda, default=str)[:1500])
        if self.financial_metrics:
            p.append("\n## Key Financial Metrics (for PE/PB derivation)")
            key_rows = ['EPS', 'PE Ratio', 'Revenue', 'EBITDA']
            p.append(self._dict_to_table(self.financial_metrics, key_rows))
        return "\n".join(p)

    def prompt_technical_analysis(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})",
             f"Current Price: ${self.current_price:.2f}" if self.current_price else "Current Price: N/A", ""]
        if self.technical_indicators:
            p.append("## Technical Indicators")
            for k, v in self.technical_indicators.items():
                p.append(f"- {k}: {v}")
        return "\n".join(p)

    def prompt_monitor_signals(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})", ""]
        if self.catalyst_data:
            p.append("## Known Catalysts")
            p.append(json.dumps(self.catalyst_data, default=str)[:1500])
        if self.risk_data:
            p.append("\n## Key Risks")
            p.append(json.dumps(self.risk_data, default=str)[:1000])
        if self.forecast_data:
            p.append("\n## Forecast Assumptions (for signal derivation)")
            p.append(json.dumps(self.forecast_data, default=str)[:1000])
        return "\n".join(p)

    def prompt_risk_disclosure(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})",
             f"Sector: {self.sector}  |  Industry: {self.industry}", ""]
        if self.risk_data:
            p.append("## Risk Assessment Data")
            p.append(json.dumps(self.risk_data, default=str)[:1500])
        if self.industry_data:
            p.append(f"\n## Industry Context")
            p.append(f"Industry: {self.industry_data.get('industry_name', '')}")
            p.append(f"Lifecycle: {self.industry_data.get('lifecycle_stage', '')}")
            p.append(f"Key Trends: {self.industry_data.get('key_trends', '')}")
        if self.company_profile:
            cp = self.company_profile
            rev = cp.get('revenue') or cp.get('total_revenue')
            p.append(f"\n## Company Snapshot")
            p.append(f"Market Cap: ${self.market_cap:.1f}B" if self.market_cap else "")
            p.append(f"Revenue: {self._fmt_num(rev)}")
        if self.valuation_results:
            p.append("\n## Valuation Context (for valuation risk assessment)")
            p.append(json.dumps(self.valuation_results, default=str)[:800])
        return "\n".join(p)

    def prompt_investment_rationale(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})",
             f"Sector: {self.sector}  |  Industry: {self.industry}",
             f"Current Price: ${self.current_price:.2f}" if self.current_price else "", ""]
        if self.financial_metrics:
            p.append("## Key Financials")
            key_rows = ['Revenue', 'Revenue Growth', 'EBITDA Margin', 'ROE', 'Net Income']
            p.append(self._dict_to_table(self.financial_metrics, key_rows))
        if self.industry_data:
            p.append(f"\n## Market Context")
            p.append(f"Market Size: {self.industry_data.get('market_size', 'N/A')}")
            p.append(f"Growth Rate: {self.industry_data.get('forecast_cagr', 'N/A')}")
        if self.peer_metrics:
            p.append("\n## Competitive Landscape")
            p.append(json.dumps(self.peer_metrics, default=str)[:1200])
        if self.module_results:
            p.append("\n## Cross-Module Insights")
            for mod in ('industry_analysis', 'financial_analysis', 'company_analysis'):
                if mod in self.module_results:
                    summary = self.module_results[mod]
                    if isinstance(summary, dict):
                        brief = {k: v for k, v in list(summary.items())[:3]}
                        p.append(f"\nFrom {mod}: {json.dumps(brief, default=str)[:600]}")
        return "\n".join(p)

    def prompt_investment_thesis(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})",
             f"Current Price: ${self.current_price:.2f}  |  Market Cap: ${self.market_cap:.1f}B" if self.current_price else "", ""]
        if self.module_results:
            p.append("## All Module Results (for synthesis)")
            for mod_name, result in self.module_results.items():
                if mod_name in ('editor', 'investment_thesis'):
                    continue
                if isinstance(result, dict):
                    # Extract key summary fields
                    key_fields = {'key_takeaway', 'summary', 'executive_summary',
                                  'final_rating', 'conclusion', 'takeaway'}
                    short = {k: v for k, v in result.items()
                             if k in key_fields or 'summary' in k.lower() or 'takeaway' in k.lower()}
                    if not short:
                        short = {k: v for k, v in list(result.items())[:3]}
                    p.append(f"\n### {mod_name}")
                    p.append(json.dumps(short, indent=2, default=str)[:800])
        return "\n".join(p)

    def prompt_editor(self) -> str:
        p = [f"Company: {self.company_name} ({self.company_ticker})", ""]
        if self.module_results:
            p.append("## All 10 Module Outputs (for review)")
            for mod_name, result in self.module_results.items():
                if mod_name == 'editor':
                    continue
                p.append(f"\n### === {mod_name} ===")
                p.append(json.dumps(result, indent=2, default=str)[:1200])
        p.append("\n\n## Original Data (for fact-checking)")
        if self.financial_metrics:
            key_rows = ['Revenue', 'Revenue Growth', 'EBITDA Margin', 'EPS', 'PE Ratio', 'ROE']
            p.append(self._dict_to_table(self.financial_metrics, key_rows))
        if self.valuation_results:
            p.append(f"\nValuation: {json.dumps(self.valuation_results, default=str)[:600]}")
        return "\n".join(p)


# ---------------------------------------------------------------------------
# Agent runner (replaces openai-agents SDK calls — uses raw Chat Completions)
# ---------------------------------------------------------------------------

_STRUCTURED_OUTPUT_SYSTEM_PROMPT = """
You must respond with valid JSON only. No markdown, no code fences, no additional text.
Your entire response must parse as a single JSON object matching the specified schema.

IMPORTANT RULES:
1. Output ONLY the JSON object — no preamble, no comments, no ```json fences
2. Every field in the schema must be present in your output
3. String values must be properly escaped (use \\\" for quotes inside strings)
4. Numbers must NOT be quoted (unless the schema says they should be strings)
5. Arrays must use [] syntax, objects must use {} syntax
6. Do not include trailing commas
""".strip()


def run_agent(
    instructions: str,
    output_schema: dict,
    user_prompt: str,
    model: str = None,
    api_key: str = None,
    base_url: str = None,
    temperature: float = 0.25,
    max_tokens: int = 4000,
) -> dict:
    """
    Run an agent using the OpenAI-compatible Chat Completions API (DeepSeek compatible).

    Uses JSON mode + structured output prompting to get Pydantic-compatible JSON.
    Also uses tool calling (function_call) with strict JSON schema for models that
    support it (gpt-4o, deepseek-chat via json_object mode).

    Args:
        instructions: The agent's system instructions
        output_schema: JSON schema dict describing the expected output
        user_prompt: The data-rich user prompt
        model: Model name
        api_key: API key
        base_url: API base URL
        temperature: Generation temperature
        max_tokens: Max output tokens

    Returns:
        Parsed JSON dict matching the output schema
    """
    model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    if not api_key:
        raise ValueError("No API key available. Set DEEPSEEK_API_KEY.")

    client = OpenAI(api_key=api_key, base_url=base_url)

    # Build system message: instructions + output schema + JSON enforcement
    schema_str = json.dumps(output_schema, indent=2)
    system_content = (
        f"{instructions}\n\n"
        f"{_STRUCTURED_OUTPUT_SYSTEM_PROMPT}\n\n"
        f"## REQUIRED JSON SCHEMA\n"
        f"Your output must conform to this JSON structure exactly:\n"
        f"```json\n{schema_str}\n```"
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_prompt},
    ]

    logger.info(f"Calling {model} with {len(user_prompt)}-char prompt...")

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},  # DeepSeek supports this
    )

    content = response.choices[0].message.content.strip()

    # Clean up common LLM artifacts
    content = _clean_json_response(content)

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}")
        logger.error(f"Raw content (first 500 chars): {content[:500]}")
        # Retry once with simpler prompt
        return _retry_json_parse(client, model, instructions, user_prompt, output_schema,
                                 temperature, max_tokens)


def _clean_json_response(content: str) -> str:
    """Strip markdown fences and other common LLM artifacts from JSON output."""
    content = content.strip()
    # Remove ```json ... ``` fences
    if content.startswith("```"):
        lines = content.split("\n")
        # Remove first line if it's ``` or ```json
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines)
    return content.strip()


def _retry_json_parse(client, model, instructions, user_prompt, schema, temperature, max_tokens) -> dict:
    """Retry with an explicit reminder to output pure JSON."""
    retry_system = (
        f"{instructions}\n\n"
        f"CRITICAL: Your last response was not valid JSON. "
        f"You MUST output ONLY a valid JSON object. Start your response with {{ and end with }}. "
        f"No markdown fences. No explanatory text. Only the JSON object.\n\n"
        f"Required schema:\n{json.dumps(schema, indent=2)}"
    )
    messages = [
        {"role": "system", "content": retry_system},
        {"role": "user", "content": user_prompt},
        # Nudge with a pre-filled assistant start
        {"role": "assistant", "content": "{"},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.1,  # even lower on retry
        max_tokens=max_tokens,
    )

    content = "{" + response.choices[0].message.content.strip()
    content = _clean_json_response(content)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.error(f"Retry also failed. Returning partial/error result.")
        return {"error": "Failed to parse agent output as JSON", "raw": content[:500]}


def schema_from_pydantic(model_class: type) -> dict:
    """Extract JSON schema from a Pydantic BaseModel class."""
    return model_class.model_json_schema()
