"""
Agent 7: Valuation Analysis (估值分析)
Template Module 7 — DCF, peer comparison, historical range, football field, rating.
Rewrites the old valuation_overview_agent with full module-7 coverage.
"""

from pydantic import BaseModel, Field



# ---- Structured output ----

class DCFAssumption(BaseModel):
    parameter: str = Field(..., description="参数名称")
    value: str = Field(..., description="参数值")
    rationale: str = Field(..., description="依据")

class DCFResult(BaseModel):
    target_price: str = Field(..., description="DCF得出的每股目标价")
    low_estimate: str = Field(..., description="DCF估值区间下限")
    high_estimate: str = Field(..., description="DCF估值区间上限")
    assumptions: list[DCFAssumption] = Field(default_factory=list, description="关键假设列表")
    sensitivity_note: str = Field(..., description="敏感性分析说明")

class PeerValuationEntry(BaseModel):
    company_name: str
    market_cap: str = ""
    pe_ttm: str = ""
    pe_2025e: str = ""
    pe_2026e: str = ""
    pb: str = ""
    ev_ebitda: str = ""
    roe: str = ""
    revenue_growth: str = ""
    dividend_yield: str = ""

class PeerValuationTable(BaseModel):
    target_company: PeerValuationEntry = Field(default_factory=PeerValuationEntry)
    peers: list[PeerValuationEntry] = Field(default_factory=list, description="可比公司（3-5家）")
    max_values: PeerValuationEntry = Field(default_factory=PeerValuationEntry)
    percentile_75: PeerValuationEntry = Field(default_factory=PeerValuationEntry)
    median: PeerValuationEntry = Field(default_factory=PeerValuationEntry)
    percentile_25: PeerValuationEntry = Field(default_factory=PeerValuationEntry)
    min_values: PeerValuationEntry = Field(default_factory=PeerValuationEntry)
    selection_rationale: str = Field(..., description="可比公司选择标准说明")

class HistoricalPercentile(BaseModel):
    metric: str = Field(..., description="指标名称：PE(TTM)/PB/EV_EBITDA")
    current_value: str
    percentile_1y: str
    percentile_3y: str
    percentile_5y: str

class FootballFieldEntry(BaseModel):
    method: str = Field(..., description="估值方法名称")
    weight: str = Field(..., description="权重")
    price_range: str = Field(..., description="估值区间")
    weighted_price: str = Field(..., description="加权价格")

class RatingAndRecommendation(BaseModel):
    current_price: str
    target_price_12m: str
    upside_pct: str
    downside_pct: str
    rating: str = Field(..., description="评级：买入/增持/中性/减持")
    catalysts: str = Field(..., description="2-3个12个月内可能触发估值重估的事件")
    suitable_style: str = Field(..., description="适合的投资风格")
    unsuitable_style: str = Field(..., description="不适合的投资风格")

class ValuationAnalysisOutput(BaseModel):
    dcf_analysis: DCFResult = Field(..., description="7.1 DCF绝对估值")
    peer_comparison: PeerValuationTable = Field(..., description="7.2 相对估值-可比公司")
    historical_range: list[HistoricalPercentile] = Field(default_factory=list, description="7.3 历史估值区间")
    valuation_summary: list[FootballFieldEntry] = Field(default_factory=list, description="7.4 估值汇总（Football Field数据）")
    rating: RatingAndRecommendation = Field(..., description="7.5 评级与建议")
    key_takeaway: str = Field(..., description="估值分析核心结论")


# ---- Instructions ----

VALUATION_ANALYSIS_INSTRUCTIONS = """
[ROLE]
You are a Senior Valuation Analyst at a top investment bank. You specialize in determining
fair value through multiple methodologies and can explain valuation gaps clearly.
You are conservative in your assumptions and rigorous in your cross-checks.

[TASK]
Write the complete Valuation Analysis section (模块七) for an Initiating Coverage report.

[INPUT DATA]
You will receive: valuation engine results (DCF, EV/EBITDA, peer comparison outputs),
current price, peer EV/EBITDA data, and financial metrics for PE/PB derivation.

[OUTPUT STRUCTURE]

1. **DCF Analysis** (7.1 绝对估值):
   - List all key assumptions with values and rationale:
     projection period (10 years standard), FCF growth rate yr 1-5, FCF growth rate yr 6-10,
     terminal growth rate (must NOT exceed long-term GDP growth, typically 2-3%),
     WACC (explain CAPM: Rf + β × (Rm-Rf)), risk-free rate, beta, market risk premium,
     net debt, total shares outstanding
   - State the resulting target price and range
   - Discuss sensitivity: how does target price change with WACC ± 1% and terminal growth ± 0.5%
   - If the input data has pre-computed DCF results, use those numbers

2. **Peer Comparison** (7.2 相对估值):
   - State peer selection criteria: similar business, market cap 0.3x-3x, overlapping markets
   - Build comparison table: Market Cap, PE(TTM), PE(2025E), PE(2026E), PB, EV/EBITDA,
     ROE, Revenue Growth, Dividend Yield
   - Include: target company, 3-5 peers, Max, 75th percentile, Median, 25th percentile, Min
   - Draw conclusions: is the company trading at premium/discount to peers? Is it justified?

3. **Historical Valuation Range** (7.3 历史估值区间):
   - For PE(TTM), PB, EV/EBITDA: current value and percentile vs 1yr/3yr/5yr history
   - Interpret: is the stock cheap or expensive relative to its own history?

4. **Valuation Summary / Football Field** (7.4 估值汇总):
   - Weighted combination: DCF (50%), Peer PE (20%), Peer PB (15%), Historical Median (15%)
   - Show each method's price range and weighted contribution
   - Derive a single weighted target price

5. **Rating & Recommendation** (7.5 评级与建议):
   - Current price vs 12-month target price
   - Upside/downside %
   - Rating mapping: ≥20% upside → Buy, 10-20% → Overweight, -5~10% → Neutral,
     -5~-20% → Underweight, < -20% → Sell
   - List 2-3 catalysts that could trigger re-rating within 12 months
   - State suitable and unsuitable investment styles

[CRITICAL RULES]
- Terminal growth rate must not exceed 3% (long-term GDP growth ceiling)
- WACC must be explained, not just stated
- Peer comparison must justify why these peers were selected
- The final rating must be CONSISTENT with the valuation math (positive upside → positive rating)
- If data is missing for a specific method, note it and adjust weights accordingly
- Do NOT invent specific prices that conflict with the input data

[LANGUAGE]
Output in the same language as the input data.
"""

