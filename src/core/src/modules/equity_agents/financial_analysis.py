"""
Agent 5: Financial Analysis (财务分析)
Template Module 5 — revenue, profitability, DuPont, operating efficiency,
cash flow, credit metrics, industry-specific KPIs.
"""

from pydantic import BaseModel, Field



# ---- Structured output ----

class RevenueAnalysis(BaseModel):
    revenue_trend: str = Field(..., description="近3-5年营收及增速分析，3-5句，含具体数字")
    revenue_mix_change: str = Field(..., description="分产品/分地区收入构成变化分析")
    volume_vs_price: str = Field(..., description="量价拆分：销量驱动还是价格驱动")

class ProfitabilityTable(BaseModel):
    """5.2 盈利能力表格 — one row per year"""
    years: list[str] = Field(..., description="年份列表，如 ['2022A','2023A','2024A','2025E','2026E']")
    gross_margin: list[str] = Field(..., description="毛利率各年值")
    ebitda_margin: list[str] = Field(..., description="EBITDA率各年值")
    net_margin: list[str] = Field(..., description="净利率各年值")
    roe: list[str] = Field(..., description="ROE各年值")
    roa: list[str] = Field(..., description="ROA各年值")
    eps: list[str] = Field(..., description="EPS各年值")

class ProfitabilityAnalysis(BaseModel):
    table: ProfitabilityTable = Field(..., description="盈利能力指标表")
    margin_attribution: str = Field(..., description="毛利率变动归因：成本结构/产品结构/定价策略的变化")
    roe_drivers: str = Field(..., description="ROE变动驱动因素分析")

class DuPontAnalysis(BaseModel):
    """5.3 杜邦分析"""
    years: list[str] = Field(default_factory=list, description="年份")
    roe_values: list[str] = Field(default_factory=list, description="ROE各年值")
    net_margin_values: list[str] = Field(default_factory=list, description="净利率各年值")
    asset_turnover_values: list[str] = Field(default_factory=list, description="资产周转率各年值")
    equity_multiplier_values: list[str] = Field(default_factory=list, description="权益乘数各年值")
    driver_conclusion: str = Field(..., description="ROE变动主要驱动因素：利润率改善/周转加快/加杠杆")

class OperatingEfficiency(BaseModel):
    """5.4 运营效率"""
    inventory_turnover: dict = Field(default_factory=dict, description="存货周转率：{year: value}")
    receivables_turnover: dict = Field(default_factory=dict, description="应收账款周转率")
    asset_turnover: dict = Field(default_factory=dict, description="总资产周转率")
    operating_cycle: dict = Field(default_factory=dict, description="营业周期（天）")
    analysis: str = Field(..., description="运营效率综合评价，2-3句")

class CashFlowAnalysis(BaseModel):
    """5.5 现金流分析"""
    operating_cf: dict = Field(default_factory=dict, description="经营性现金流：{year: value}")
    capex: dict = Field(default_factory=dict, description="资本开支：{year: value}")
    fcf: dict = Field(default_factory=dict, description="自由现金流：{year: value}")
    fcf_to_net_income: dict = Field(default_factory=dict, description="FCF/净利润：{year: value}")
    fcf_margin: dict = Field(default_factory=dict, description="FCF率：{year: value}")
    health_assessment: str = Field(..., description="现金流健康度评价")
    coverage_assessment: str = Field(..., description="FCF能否覆盖分红和资本开支")

class CreditMetrics(BaseModel):
    """5.6 偿债能力与资本结构"""
    debt_to_asset: dict = Field(default_factory=dict, description="资产负债率")
    current_ratio: dict = Field(default_factory=dict, description="流动比率")
    quick_ratio: dict = Field(default_factory=dict, description="速动比率")
    interest_coverage: dict = Field(default_factory=dict, description="利息保障倍数")
    net_debt_to_ebitda: dict = Field(default_factory=dict, description="净负债/EBITDA")
    overall_assessment: str = Field(..., description="偿债能力综合结论")

class IndustrySpecificKPI(BaseModel):
    """5.7 行业特定核心运营指标"""
    industry_type: str = Field(..., description="行业类型：银行/保险/消费品/SaaS/制造业/房地产/其他")
    kpis: list[dict] = Field(default_factory=list, description="3-5个行业特定指标，每个包含 name + value + interpretation")

class FinancialAnalysisOutput(BaseModel):
    revenue_analysis: RevenueAnalysis = Field(..., description="5.1 收入分析")
    profitability_analysis: ProfitabilityAnalysis = Field(..., description="5.2 盈利能力分析")
    dupont_analysis: DuPontAnalysis = Field(..., description="5.3 杜邦分析")
    operating_efficiency: OperatingEfficiency = Field(..., description="5.4 运营效率")
    cash_flow_analysis: CashFlowAnalysis = Field(..., description="5.5 现金流分析")
    credit_metrics: CreditMetrics = Field(..., description="5.6 偿债能力与资本结构")
    industry_kpis: IndustrySpecificKPI = Field(default_factory=lambda: IndustrySpecificKPI(industry_type="其他"), description="5.7 行业特定指标")
    key_takeaway: str = Field(..., description="财务分析核心结论，3-5句")


# ---- Instructions ----

FINANCIAL_ANALYSIS_INSTRUCTIONS = """
[ROLE]
You are a Senior Financial Analyst (CFA charterholder) at a bulge-bracket investment bank.
You have 12 years of experience in forensic financial analysis. You can spot earnings
quality issues, understand capital allocation efficiency, and explain financial trends
with clarity and precision.

[TASK]
Write the complete Financial Analysis section (模块五) for an Initiating Coverage report.

[INPUT DATA]
You will receive: financial metrics table (historical + forecast), balance sheet data,
cash flow data. Use the provided numbers — do NOT fabricate data.

[OUTPUT STRUCTURE]

1. **Revenue Analysis** (5.1 收入分析):
   - Analyze the 3-5 year revenue trajectory with specific growth rates
   - Discuss product/geographic mix changes if data permits
   - Assess volume-driven vs price-driven growth

2. **Profitability Analysis** (5.2 盈利能力分析):
   - Fill the profitability table with actual data from the input
   - Attribute gross margin changes: cost structure vs product mix vs pricing
   - Explain ROE changes through a DuPont lens

3. **DuPont Analysis** (5.3 杜邦分析):
   - Decompose ROE = Net Margin × Asset Turnover × Equity Multiplier
   - State clearly whether ROE changes are driven by margin improvement,
     efficiency gains, or increased leverage (this is critical for quality assessment)

4. **Operating Efficiency** (5.4 运营效率):
   - Report inventory turnover, receivables turnover, asset turnover, operating cycle
   - Comment on working capital management trends

5. **Cash Flow Analysis** (5.5 现金流分析):
   - Operating CF, CapEx, FCF, FCF/Net Income, FCF margin
   - Assess cash flow health: is operating CF sustainable? Can FCF cover dividends + CapEx?

6. **Credit Metrics** (5.6 偿债能力):
   - Debt/Asset, Current Ratio, Quick Ratio, Interest Coverage, Net Debt/EBITDA
   - Overall assessment of balance sheet strength

7. **Industry-Specific KPIs** (5.7 核心运营指标):
   - Identify the company's industry type
   - Select and report 3-5 industry-specific KPIs:
     * Banks: NIM, NPL ratio, coverage ratio, CAR, LDR
     * Insurance: combined ratio, NBV margin, embedded value
     * Consumer: same-store growth, SKU count, sales per sqft
     * SaaS/Software: ARR, NRR, LTV/CAC
     * Manufacturing: capacity utilization, production-to-sales ratio, revenue per employee
     * Real Estate: sales area, sell-through rate, land bank, financing cost

[CRITICAL RULES]
- Every number in the output MUST come from the input data — do not invent financial figures
- If a metric is not in the data, say "Not available from current data" rather than guessing
- Express margins and ratios with proper units (%, x, days)
- The DuPont conclusion must be specific: "ROE increased from X% to Y%, primarily driven by..."
- Cash flow analysis must state clearly whether the company can self-fund its operations

[LANGUAGE]
Output in the same language as the input data.
"""

