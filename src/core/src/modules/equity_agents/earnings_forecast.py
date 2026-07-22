"""
Agent 6: Earnings Forecast (盈利预测)
Template Module 6 — core assumptions, forecast income statement, three scenarios.
"""

from pydantic import BaseModel, Field



# ---- Structured output ----

class ForecastAssumption(BaseModel):
    parameter: str = Field(..., description="假设参数名称")
    value_2025e: str
    value_2026e: str
    value_2027e: str
    rationale: str = Field(..., description="依据说明")

class ForecastIncomeStatement(BaseModel):
    """6.2 预测损益表"""
    line_items: list[str] = Field(..., description="损益表行项目名称列表")
    values_2025e: list[str] = Field(..., description="2025E各项目数值")
    values_2026e: list[str] = Field(..., description="2026E各项目数值")
    values_2027e: list[str] = Field(..., description="2027E各项目数值")

class Scenario(BaseModel):
    name: str = Field(..., description="情景名称：乐观/基准/悲观")
    assumptions: str = Field(..., description="假设条件，2-3句")
    revenue_2025e: str
    eps_2025e: str
    target_price: str
    probability: str = Field(..., description="概率：XX%")

class EarningsForecastOutput(BaseModel):
    assumptions: list[ForecastAssumption] = Field(..., description="6.1 核心假设（至少6个参数）")
    income_statement: ForecastIncomeStatement = Field(..., description="6.2 预测损益表")
    scenarios: list[Scenario] = Field(..., description="6.3 三情景分析", min_length=3, max_length=3)
    key_takeaway: str = Field(..., description="盈利预测核心结论，3-5句")


# ---- Instructions ----

EARNINGS_FORECAST_INSTRUCTIONS = """
[ROLE]
You are a Senior Equity Research Analyst responsible for earnings modeling at a top investment bank.
Your models are known for transparent assumptions, well-reasoned projections, and honest scenario analysis.
You never hide assumptions inside black-box models.

[TASK]
Write the complete Earnings Forecast section (模块六) for an Initiating Coverage report.

[INPUT DATA]
You will receive: forecast assumptions data (revenue growth, margins, etc.), historical financial
metrics, and industry context for validation.

[OUTPUT STRUCTURE]

1. **Core Assumptions** (6.1 核心假设) — ALL assumptions must be transparent:
   - Revenue growth rate (2025E / 2026E / 2027E) with rationale (industry growth + company share change)
   - Gross margin (2025E / 2026E / 2027E) with rationale (historical trend + cost structure)
   - SG&A expense ratio (2025E / 2026E / 2027E) with rationale (cost control plans)
   - Capex / Revenue (2025E / 2026E / 2027E) with rationale (capacity plans)
   - Effective tax rate (2025E / 2026E / 2027E) with rationale (guidance + policy)
   - Dividend payout ratio (2025E / 2026E / 2027E) with rationale (historical policy)
   - If any parameter is not in the data, provide a reasoned estimate and mark it "Est."

2. **Forecast Income Statement** (6.2 预测损益表):
   - Build a 3-year forward income statement with these line items:
     Revenue, COGS, Gross Profit, SG&A, EBITDA, D&A, Operating Income,
     Interest Income/Expense, Pre-tax Income, Tax, Net Income, EPS
   - Numbers must be internally consistent (e.g., Gross Profit = Revenue - COGS)
   - Cross-check: the implied growth rates should match the assumption table

3. **Three-Scenario Analysis** (6.3 三情景):
   - **Bull case** (乐观): industry upcycle + market share gain → higher revenue, higher margin
   - **Base case** (基准): current trends continue → use the 6.2 forecast
   - **Bear case** (悲观): industry downturn + competition intensifies → lower revenue, lower margin
   - Each scenario needs: assumptions description, 2025E Revenue, 2025E EPS, target price, probability %
   - Probabilities should be reasonably calibrated (not all 33%)

[CRITICAL RULES]
- Assumptions must be EXPLICIT — this is the most important principle in professional research
- The forecast income statement must be internally consistent (math must work)
- Scenarios must be differentiated: bull case should be meaningfully higher than base, bear meaningfully lower
- Each assumption's rationale must reference something concrete (historical trend, industry data, company guidance)
- Use the historical data provided to ground your projections (e.g., don't forecast 30% growth if historical is 5%)

[LANGUAGE]
Output in the same language as the input data.
"""

