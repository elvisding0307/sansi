"""Equity Research Agents — 10+1 agent system for Initiating Coverage reports."""

# Infrastructure
from .base import ModuleData, create_llm, schema_from_pydantic
from .agent_manager import EquityResearchAgentManager, create_manager

# Output types (for type checking / reference)
from .industry_analysis import IndustryAnalysisOutput
from .company_analysis import CompanyAnalysisOutput
from .financial_analysis import FinancialAnalysisOutput
from .earnings_forecast import EarningsForecastOutput
from .valuation_analysis import ValuationAnalysisOutput
from .technical_analysis import TechnicalAnalysisOutput
from .investment_rationale import InvestmentRationaleOutput
from .risk_disclosure import RiskDisclosureOutput
from .monitor_signals import MonitorSignalsOutput
from .investment_thesis import InvestmentThesisOutput
from .editor import EditorOutput

# Instructions (for reference / customization)
from .industry_analysis import INDUSTRY_ANALYSIS_INSTRUCTIONS
from .company_analysis import COMPANY_ANALYSIS_INSTRUCTIONS
from .financial_analysis import FINANCIAL_ANALYSIS_INSTRUCTIONS
from .earnings_forecast import EARNINGS_FORECAST_INSTRUCTIONS
from .valuation_analysis import VALUATION_ANALYSIS_INSTRUCTIONS
from .technical_analysis import TECHNICAL_ANALYSIS_INSTRUCTIONS
from .investment_rationale import INVESTMENT_RATIONALE_INSTRUCTIONS
from .risk_disclosure import RISK_DISCLOSURE_INSTRUCTIONS
from .monitor_signals import MONITOR_SIGNALS_INSTRUCTIONS
from .investment_thesis import INVESTMENT_THESIS_INSTRUCTIONS
from .editor import EDITOR_INSTRUCTIONS

# Legacy agents (backward compatible — simple text agents)
from .tagline_agent import tagline_agent, TaglineResponse
from .company_overview_agent import company_overview_agent, CompanyOverviewResponse
from .investment_overview_agent import investment_overview_agent, InvestmentOverviewResponse
from .valuation_overview_agent import valuation_overview_agent, ValuationOverviewResponse
from .risks_agent import risks_agent, RisksResponse
from .competitor_analysis_agent import competitor_analysis_agent, CompetitorAnalysisResponse
from .major_takeaways_agent import major_takeaways_agent, MajorTakeawaysResponse
from .news_summary_agent import news_summary_agent, NewsSummaryResponse

__all__ = [
    # Infrastructure
    "ModuleData",
    "create_llm",
    "schema_from_pydantic",
    "EquityResearchAgentManager",
    "create_manager",
    # Output types
    "IndustryAnalysisOutput",
    "CompanyAnalysisOutput",
    "FinancialAnalysisOutput",
    "EarningsForecastOutput",
    "ValuationAnalysisOutput",
    "TechnicalAnalysisOutput",
    "InvestmentRationaleOutput",
    "RiskDisclosureOutput",
    "MonitorSignalsOutput",
    "InvestmentThesisOutput",
    "EditorOutput",
    # Instructions
    "INDUSTRY_ANALYSIS_INSTRUCTIONS",
    "COMPANY_ANALYSIS_INSTRUCTIONS",
    "FINANCIAL_ANALYSIS_INSTRUCTIONS",
    "EARNINGS_FORECAST_INSTRUCTIONS",
    "VALUATION_ANALYSIS_INSTRUCTIONS",
    "TECHNICAL_ANALYSIS_INSTRUCTIONS",
    "INVESTMENT_RATIONALE_INSTRUCTIONS",
    "RISK_DISCLOSURE_INSTRUCTIONS",
    "MONITOR_SIGNALS_INSTRUCTIONS",
    "INVESTMENT_THESIS_INSTRUCTIONS",
    "EDITOR_INSTRUCTIONS",
    # Legacy
    "tagline_agent", "company_overview_agent", "investment_overview_agent",
    "valuation_overview_agent", "risks_agent", "competitor_analysis_agent",
    "major_takeaways_agent", "news_summary_agent",
]
