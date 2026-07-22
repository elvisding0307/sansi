"""
Agent 4: Company Analysis (公司分析)
Template Module 4 — business model, management, segments, moat, growth drivers.
Rewrites the old company_overview_agent with full module-4 coverage.
"""

from pydantic import BaseModel, Field



# ---- Structured output ----

class CompanyOverview(BaseModel):
    one_liner: str = Field(..., description="一句话描述：公司是干什么的")
    business_model: str = Field(..., description="怎么赚钱：收入来源、成本结构、盈利模式，3-5句")
    customers: str = Field(..., description="客户是谁：目标客群、客户结构")
    scale: str = Field(..., description="规模：营收、利润、员工数、网点/分支机构")
    ownership: str = Field(..., description="股权结构：实际控制人、前十大股东、机构持股比例")

class Milestone(BaseModel):
    year: str = Field(..., description="年份")
    event: str = Field(..., description="事件描述")
    significance: str = Field(default="", description="重要性说明")

class Executive(BaseModel):
    name: str
    title: str
    tenure: str = ""
    background: str = Field(default="", description="从业背景与核心履历")
    shareholding: str = Field(default="", description="持股情况及薪酬结构")

class Governance(BaseModel):
    board_structure: str = Field(default="", description="董事会结构（独立董事占比）")
    equity_incentives: str = Field(default="", description="股权激励覆盖范围与行权条件")
    dividend_history: str = Field(default="", description="历史分红记录与分红率")
    related_party: str = Field(default="", description="关联交易与信息披露质量评价")

class BusinessSegment(BaseModel):
    name: str = Field(..., description="业务板块名称")
    revenue: str = Field(..., description="收入")
    revenue_share: str = Field(..., description="收入占比")
    yoy_growth: str = Field(..., description="同比增速")
    gross_margin: str = Field(default="", description="毛利率")
    key_driver: str = Field(default="", description="核心驱动因素")

class MoatAnalysis(BaseModel):
    brand_barrier: str = Field(default="", description="品牌/牌照壁垒")
    tech_barrier: str = Field(default="", description="技术/专利壁垒")
    channel_barrier: str = Field(default="", description="渠道/网络壁垒")
    scale_barrier: str = Field(default="", description="规模/成本壁垒")
    switching_cost: str = Field(default="", description="客户粘性/转换成本")
    overall_moat_rating: str = Field(..., description="综合护城河评级：宽阔/狭窄/无 + 1-2句总结")

class GrowthDriver(BaseModel):
    driver_name: str = Field(..., description="驱动因素名称")
    current_status: str = Field(..., description="当前状态")
    incremental_opportunity: str = Field(..., description="增量空间")
    timeline: str = Field(..., description="预期兑现时间节点")

class CustomerAnalysis(BaseModel):
    customer_segments: str = Field(default="", description="客户分群与占比")
    top5_concentration: str = Field(default="", description="前五大客户集中度")
    cac_ltv: str = Field(default="", description="获客成本与客户生命周期价值")
    retention: str = Field(default="", description="净收入留存率/流失率")
    channel_mix: str = Field(default="", description="销售渠道分布")

class CompanyAnalysisOutput(BaseModel):
    company_overview: CompanyOverview = Field(..., description="4.1 公司概况")
    milestones: list[Milestone] = Field(default_factory=list, description="4.2 发展历程（5-8个关键节点）")
    executives: list[Executive] = Field(default_factory=list, description="4.3 管理层（CEO/CFO/核心业务负责人）")
    governance: Governance = Field(default_factory=Governance, description="4.3 治理结构评价")
    business_segments: list[BusinessSegment] = Field(default_factory=list, description="4.4 主营业务拆分")
    moat_analysis: MoatAnalysis = Field(..., description="4.5 核心竞争力（护城河）")
    short_term_drivers: list[GrowthDriver] = Field(default_factory=list, description="4.6 短期驱动（1-2年），2-3个")
    medium_term_drivers: list[GrowthDriver] = Field(default_factory=list, description="4.6 中期驱动（3-5年），1-2个")
    customer_analysis: CustomerAnalysis = Field(default_factory=CustomerAnalysis, description="4.7 客户与渠道")


# ---- Instructions ----

COMPANY_ANALYSIS_INSTRUCTIONS = """
[ROLE]
You are a Senior Equity Research Analyst specializing in company deep-dives.
Your Initiating Coverage reports are the gold standard for understanding a company's
business quality, competitive moat, and growth trajectory.

[TASK]
Write the complete Company Analysis section (模块四) for an Initiating Coverage report.

[INPUT DATA]
You will receive: company profile, management team details, business segment breakdown,
historical milestones, and industry/sector classification.

[OUTPUT STRUCTURE]
You must fill ALL sections below with specific, quantified analysis:

1. **Company Overview** (公司概况 4.1):
   - One-liner: what the company does, in one sentence
   - Business model: revenue sources, cost structure, profit model (3-5 sentences)
   - Customers: target segments, customer structure
   - Scale: revenue, profit, employee count, branches/locations
   - Ownership: controlling shareholders, top institutional holders

2. **Milestones** (发展历程 4.2): 5-8 key events with years and significance

3. **Management & Governance** (管理层与治理 4.3):
   - CEO, CFO, key business heads: name, title, tenure, background, shareholding
   - Board structure (independent director ratio)
   - Equity incentive coverage
   - Dividend history and payout ratio; related-party transaction quality

4. **Business Segments** (主营业务拆分 4.4):
   - For each segment: name, revenue, revenue share %, YoY growth %, gross margin, key driver
   - Include a "Total" row

5. **Moat Analysis** (核心竞争力 4.5):
   - Evaluate all five moat dimensions: brand/license, tech/patent, channel/network,
     scale/cost, customer switching cost
   - Give an overall moat rating: Wide / Narrow / None, with a 1-2 sentence justification

6. **Growth Drivers** (成长驱动 4.6):
   - Short-term (1-2 years): 2-3 drivers with current status → incremental opportunity → timeline
   - Medium-term (3-5 years): 1-2 drivers

7. **Customer & Channel** (客户与渠道 4.7):
   - Customer segments and concentration (top 5)
   - CAC, LTV, LTV/CAC ratio if applicable
   - Net revenue retention / churn
   - Sales channel mix (direct / distributor / online / other)

[QUALITY STANDARDS]
- Every claim about the company's position must have data backing
- Business segment breakdown must sum to ~100%
- Moat analysis must reference specific competitive advantages, not generic statements
- Growth drivers must include quantification ("$X Bn opportunity" not "large opportunity")
- If specific data is unavailable, use your knowledge to provide reasonable estimates marked as "Est."

[LANGUAGE]
Output in the same language as the input data.
"""

