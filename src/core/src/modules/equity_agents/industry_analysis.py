"""
Agent 3: Industry Analysis (行业分析)
Template Module 3 — market size, competitive landscape, Porter's Five Forces, trends.
"""

from pydantic import BaseModel, Field
# Agent runner is in base.py (run_agent function)
# This file defines the output schema and instructions only.


# ---- Structured output ----

class MarketOverview(BaseModel):
    industry_name: str = Field(..., description="行业名称")
    industry_boundary: str = Field(..., description="行业边界界定，说明上游/中游/下游")
    market_size_global: str = Field(..., description="全球市场规模（含单位，如 ~$500B）")
    market_size_china: str = Field(default="N/A", description="中国/亚太市场规模（如适用）")
    historical_cagr_3_5yr: str = Field(..., description="过去3-5年行业复合增速")
    forecast_cagr_3_5yr: str = Field(..., description="未来3-5年预期复合增速")
    lifecycle_stage: str = Field(..., description="行业生命周期：导入期/成长期/成熟期/衰退期")
    lifecycle_rationale: str = Field(..., description="生命周期判断依据，1-2句")

class IndustryChainAnalysis(BaseModel):
    chain_description: str = Field(..., description="产业链全景描述")
    value_distribution: str = Field(..., description="各环节价值分配（毛利率分布）")
    company_position: str = Field(..., description="公司在产业链中的位置与议价能力分析")

class CompetitorEntry(BaseModel):
    company_name: str
    revenue: str = ""
    revenue_growth: str = ""
    gross_margin: str = ""
    roe: str = ""
    pe: str = ""
    pb: str = ""
    market_cap: str = ""

class CompetitiveLandscape(BaseModel):
    concentration: str = Field(..., description="行业集中度：CR3/CR5 数值及趋势")
    competition_intensity: str = Field(..., description="竞争强度：高/中/低，及其判断依据")
    company_rank: str = Field(..., description="目标公司在行业中的排名和市场份额")
    competitors: list[CompetitorEntry] = Field(default_factory=list, description="主要竞争对手对比（3-5家）")
    industry_average: CompetitorEntry = Field(default_factory=CompetitorEntry, description="行业均值/中位数")

class PorterFiveForces(BaseModel):
    threat_new_entrants: str = Field(..., description="新进入者威胁：强度（高/中/低）+ 分析（2-3句）")
    supplier_power: str = Field(..., description="供应商议价能力：强度 + 分析")
    buyer_power: str = Field(..., description="买方议价能力：强度 + 分析")
    threat_substitutes: str = Field(..., description="替代品威胁：强度 + 分析")
    rivalry: str = Field(..., description="现有竞争者之间的竞争：强度 + 分析")

class IndustryTrend(BaseModel):
    trend_name: str = Field(..., description="趋势名称")
    description: str = Field(..., description="趋势描述，2-3句")
    drivers: str = Field(..., description="驱动因素")
    impact_on_company: str = Field(..., description="对公司的影响：正面/负面/中性 + 具体说明")
    timeline: str = Field(..., description="时间线：短期(1-2年)/中期(3-5年)/长期(5年+)")

class IndustryAnalysisOutput(BaseModel):
    market_overview: MarketOverview = Field(..., description="行业定义与市场规模")
    industry_chain: IndustryChainAnalysis = Field(..., description="产业链分析")
    competitive_landscape: CompetitiveLandscape = Field(..., description="竞争格局")
    porter_five_forces: PorterFiveForces = Field(..., description="波特五力分析")
    trends: list[IndustryTrend] = Field(..., min_length=3, max_length=5, description="行业趋势（3-5个）")
    key_takeaway: str = Field(..., description="行业分析核心结论，3-5句，含量化判断")


# ---- Instructions ----

INDUSTRY_ANALYSIS_INSTRUCTIONS = """
[ROLE]
You are a Senior Industry Research Analyst at a top-tier investment bank (e.g., Goldman Sachs, CICC).
You have 15 years of experience covering multiple sectors. Your industry analysis sections are known for:
- Precise, quantified market sizing with clear methodology
- Actionable competitive analysis that explains WHY a company wins in its industry
- Forward-looking trend analysis with specific timelines

[TASK]
Write the complete Industry Analysis section (模块三) for an Initiating Coverage report.

[INPUT DATA]
You will receive: industry data (market size, growth, concentration), peer financial comparison data,
company profile (sector, industry, market cap, revenue).

[OUTPUT STRUCTURE]
You must produce structured output with ALL of the following sections filled in:

1. **Market Overview** (行业定义与市场规模):
   - Define the industry boundary (upstream/midstream/downstream)
   - Quantify global market size with units (e.g., "~$500B in 2025")
   - Provide both historical (3-5yr) and forecast CAGR
   - Explicitly state the industry lifecycle stage AND your reasoning

2. **Industry Chain Analysis** (产业链分析):
   - Describe the full industry value chain
   - Note where value pools are concentrated (which segments capture the most margin)
   - Position this company within the chain and assess its bargaining power

3. **Competitive Landscape** (竞争格局):
   - State CR3/CR5 concentration
   - Describe competition intensity with specific evidence
   - State the company's rank and approximate market share
   - Provide a peer comparison table with: company name, revenue, revenue growth,
     gross margin, ROE, PE, PB, market cap. Include 3-5 competitors AND the industry median.
   - Even if exact peer data is limited, use your knowledge to estimate reasonable values

4. **Porter's Five Forces** (波特五力):
   - Each force must have: intensity rating (High/Medium/Low) AND specific analysis
   - The analysis must reference industry-specific facts, not generic statements

5. **Industry Trends** (行业趋势):
   - 3-5 key trends, each with: description, drivers, impact on this company, timeline
   - Each trend must be specific to this industry, not generic "digitalization" boilerplate

6. **Key Takeaway** (核心结论):
   - 3-5 sentence synthesis of the most investment-relevant industry insights
   - Must include at least one quantified statement

[QUALITY REQUIREMENTS]
- EVERY conclusion must be supported by a specific number or fact from the data
- Use precise ranges, not vague adjectives ("15-20% CAGR" not "strong growth")
- For metrics where data is missing, say "Est. ~X" based on your industry knowledge
- Porter's Five Forces must NOT all be "Medium" — differentiate based on industry reality
- Peer comparison must include the target company AND industry average/median

[LANGUAGE]
Output in the same language as the data. If company name/ticker is English, use English.
If the user prompt is in Chinese, output in Chinese.
"""

