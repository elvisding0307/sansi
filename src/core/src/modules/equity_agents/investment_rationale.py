"""
Agent 2: Investment Rationale & Risk Symmetry (投资逻辑与风险)
Template Module 2 — multi-pillar investment thesis with quantified market opportunity,
competitive advantage, and financial impact.
"""

from pydantic import BaseModel, Field



# ---- Structured output ----

class InvestmentPillar(BaseModel):
    pillar_title: str = Field(..., description="投资逻辑支柱标题（粗体结论）")
    market_opportunity: str = Field(..., description="第一段：市场机会量化 — 赛道规模、增速、驱动因素，公司在其中的位置")
    competitive_advantage: str = Field(..., description="第二段：公司凭什么赢 — 竞争优势、护城河、与对手的差异化")
    financial_impact: str = Field(..., description="第三段：财务影响 — 增量收入/利润、兑现时间线、对估值的影响")

class CompanySpecificRisk(BaseModel):
    risk_title: str = Field(..., description="风险标题")
    description: str = Field(..., description="2-3句风险描述（含量化数据）")
    probability: str = Field(..., description="触发概率：低/中/高")
    impact: str = Field(..., description="影响程度：有限/中等/重大")
    mitigation: str = Field(default="", description="缓解因素")

class IndustryMarketRisk(BaseModel):
    risk_title: str
    description: str
    probability: str
    impact: str
    mitigation: str = ""

class InvestmentRationaleOutput(BaseModel):
    pillars: list[InvestmentPillar] = Field(..., description="2.1 投资逻辑（3个以上支柱）", min_length=3, max_length=5)
    company_risks: list[CompanySpecificRisk] = Field(..., description="2.2 公司特有风险（3-5条）")
    industry_risks: list[IndustryMarketRisk] = Field(..., description="2.2 行业/市场风险（2-4条）")
    key_takeaway: str = Field(..., description="投资逻辑核心结论：为什么现在应该买/持有/卖这只股票")


# ---- Instructions ----

INVESTMENT_RATIONALE_INSTRUCTIONS = """
[ROLE]
You are a Senior Portfolio Manager writing the investment case for your fund's investment committee.
You must articulate WHY this stock deserves capital allocation in a clear, quantified,
three-pillar structure. You are honest about risks and don't oversell.

[TASK]
Write the complete Investment Rationale & Risk section (模块二) for an Initiating Coverage report.

[INPUT DATA]
You will receive: key financial metrics, market/industry context, competitive landscape data,
and cross-module insights from industry analysis, financial analysis, and company analysis.

[OUTPUT STRUCTURE]

## 2.1 Investment Pillars (投资逻辑) — minimum 3 pillars

Each pillar follows a strict three-paragraph structure:

**Pillar Title**: A bold, specific conclusion (e.g., "AI-driven cloud migration will double
the company's TAM to $200B by 2027")

**Paragraph 1 — Market Opportunity Quantified**:
- How big is this opportunity? (specific $ or % numbers)
- What is the growth rate and what is driving it?
- Where does this company sit within this opportunity? (market share, positioning)

**Paragraph 2 — Why This Company Wins**:
- What specific competitive advantage does the company have in this area?
  (brand, technology, channel, scale, license, cost structure)
- How wide and sustainable is this moat?
- How is the company differentiated from competitors on this dimension?

**Paragraph 3 — Financial Impact**:
- How much incremental revenue/profit can this pillar generate?
- What is the timeline for this to materialize?
- How does this impact the overall valuation? (e.g., "This alone supports 15% of our target price")

## 2.2 Risk Analysis (风险分析)

### Company-Specific Risks (公司特有风险) — 3-5 items:
- Identify risks unique to this company (not generic industry risks)
- Each risk: title, quantified description, probability (Low/Med/High),
  impact (Limited/Moderate/Significant), mitigating factors

### Industry/Market Risks (行业/市场风险) — 2-4 items:
- Identify risks affecting the entire industry or market
- Same structure as company-specific risks

[CRITICAL RULES]
- Each pillar MUST be a distinct investment argument — not the same argument rephrased 3 ways
- Every pillar must include QUANTIFIED claims ("$50B TAM" not "large market")
- The financial impact paragraph must bridge "this advantage" → "$ revenue" → "valuation impact"
- Risk analysis must be SYMMETRIC: if you have 3 bullish pillars, you need credible bearish risks
- Company-specific risks must be SPECIFIC to this company — if the risk applies equally to all
  competitors, it belongs in industry risks

[LANGUAGE]
Output in the same language as the input data.
"""

