"""
Agent 1: Investment Thesis (投资概要)
Template Module 1 — the most important page: rating, target price, core theses, financial snapshot.
This is written LAST but placed FIRST in the report.
"""

from pydantic import BaseModel, Field



# ---- Structured output ----

class RatingBox(BaseModel):
    rating: str = Field(..., description="评级：买入/增持/中性/减持")
    current_price: str = Field(..., description="最新价（日期）")
    target_price: str = Field(..., description="目标价")
    week_52_range: str = Field(default="N/A", description="52周区间")
    total_market_cap: str = Field(..., description="总市值")
    float_market_cap: str = Field(default="N/A", description="流通市值")

class CoreThesis(BaseModel):
    thesis_title: str = Field(..., description="粗体结论，一句话")
    expansion: str = Field(..., description="3-5句展开，含具体数据、同比环比、行业均值对比")

class FinancialSnapshot(BaseModel):
    """1.4 财务与估值快照表"""
    years: list[str] = Field(..., description="列名：['2023A','2024A','2025E','2026E','2027E']")
    revenue: list[str] = Field(..., description="营业收入各年值")
    revenue_growth: list[str] = Field(..., description="营收增速各年值")
    net_income: list[str] = Field(..., description="归母净利润各年值")
    net_income_growth: list[str] = Field(..., description="净利润增速各年值")
    gross_margin: list[str] = Field(..., description="毛利率各年值")
    ebitda_margin: list[str] = Field(..., description="EBITDA率各年值")
    roe: list[str] = Field(..., description="ROE各年值")
    eps: list[str] = Field(..., description="EPS各年值")
    pe: list[str] = Field(..., description="PE各年值")
    pb: list[str] = Field(..., description="PB各年值")
    ev_ebitda: list[str] = Field(..., description="EV/EBITDA各年值")
    dividend_yield: list[str] = Field(default_factory=list, description="股息率各年值")

class InvestmentThesisOutput(BaseModel):
    rating_box: RatingBox = Field(..., description="1.1 评级框")
    core_theses: list[CoreThesis] = Field(..., description="1.3 核心论点（3-4条）", min_length=3, max_length=4)
    financial_snapshot: FinancialSnapshot = Field(..., description="1.4 财务与估值快照表")
    executive_summary: str = Field(..., description="看完这一页就能做投资决策的执行摘要，200-300字")


# ---- Instructions ----

INVESTMENT_THESIS_INSTRUCTIONS = """
[ROLE]
You are the Director of Research at a top investment bank. You personally write the first page
of every Initiating Coverage report. This page is what portfolio managers actually read —
if it doesn't convince them in 90 seconds, they won't read the rest.

Your writing is: conclusions-first, data-dense, and brutally honest. No marketing fluff.

[TASK]
Write the complete Investment Thesis section (模块一) for an Initiating Coverage report.

[INPUT DATA]
You will receive: ALL module outputs (industry, company, financial, earnings, valuation,
technical, risk, signals). Your job is to synthesize the most important conclusions from
each module into ONE compelling page. You also receive the original financial data for
fact-checking.

[OUTPUT STRUCTURE]

## 1.1 Rating Box (评级框):
- Rating: Buy / Overweight / Neutral / Underweight / Sell
- Current price (with date)
- 12-month target price
- 52-week range
- Total market cap and float market cap

## 1.3 Core Theses (核心论点) — 3-4 items:
Each thesis is structured as:
- **Bold conclusion** (one sentence, specific)
- 3-5 sentence expansion with specific numbers, YoY comparisons, and industry benchmarks

Example structure (do NOT copy, create company-specific theses):
"Thesis 1: Revenue growth will accelerate from 5% to 12% by 2026E, driven by..."
"Thesis 2: EBITDA margins can expand 300bp to 28% through cost restructuring..."
"Thesis 3: Current valuation of 15x PE is at a 40% discount to the 5-year median..."

The theses must be differentiated — one on growth, one on profitability/quality,
one on valuation/catalyst. Do not write three variations of "the company is good."

## 1.4 Financial & Valuation Snapshot (财务与估值快照表):
Fill a table with these rows across years 2023A / 2024A / 2025E / 2026E / 2027E:
Revenue, Revenue Growth %, Net Income, Net Income Growth %, Gross Margin %,
EBITDA Margin %, ROE %, EPS, PE (x), PB (x), EV/EBITDA (x), Dividend Yield %

Use data from the financial_analysis and earnings_forecast modules. Cross-check
for consistency — revenue in the snapshot must match what the financial analysis says.

## Executive Summary (执行摘要):
200-300 words that synthesize the entire investment case:
- What the company does (one sentence)
- Why we are initiating coverage now
- The investment case in 3-4 sentences (growth + quality + valuation catalyst)
- Key risks that could break the thesis
- Final verdict: rating + target price + upside

[CRITICAL RULES]
- This page is WRITTEN LAST, after all other modules are complete
- The financial snapshot numbers MUST match the other modules exactly — cross-check
- Every thesis must have a counterpoint implied (what would prove it wrong?)
- The rating MUST be consistent with the valuation module's upside calculation
- The executive summary should be readable standalone — imagine it's the only page
  a busy PM reads

[LANGUAGE]
Output in the same language as the input data.
"""

