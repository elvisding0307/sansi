# Phase 1 详细实施方案：核心报告质量提升

> 版本：v1.0 | 日期：2026-07-22 | 预计工期：4 周

---

## 目录

1. [总览与目标](#一总览与目标)
2. [Week 1-2：数据层增强 + Agent 系统重构](#二week-1-2数据层增强--agent-系统重构)
3. [Week 3：补全缺失模块 + 估值模型升级](#三week-3补全缺失模块--估值模型升级)
4. [Week 4：质量保障 + 评测基准](#四week-4质量保障--评测基准)
5. [文件变更清单](#五文件变更清单)
6. [验收标准](#六验收标准)

---

## 一、总览与目标

### 1.1 当前架构问题

```
当前数据流：
  FMP API / yfinance
       ↓
  financial_data_processor.py  →  提取 11 个指标  →  CSV 文件
       ↓
  text_generator_agents.py      →  8 段简单 LLM 文本  →  TXT 文件
       ↓
  create_equity_report.py       →  图表 + HTML 模板  →  HTML/PDF
```

核心问题：

1. **所有数据 dump 进一个 prompt**：`_prepare_user_prompt()` 把 financial_metrics、peer_ebitda、peer_ev_ebitda、news 全塞进 user prompt，LLM 无法区分关键信息和噪音
2. **没有模块专属数据**：行业分析需要行业规模/竞争格局数据（但没有数据源），技术面分析需要技术指标计算（有计算但无 LLM 文字分析），公司分析需要管理层/业务拆分数据（没有数据源）
3. **输出无结构约束**：system prompt 只说 "write a company overview (300-400 words)"，没有要求引用具体数字，没有输出格式规范
4. **两套 agent 系统**：`text_generator_agents.py`（在用）和 `equity_agents/`（闲置）各写了一遍
5. **估值模型硬编码**：WACC = 10%、net_debt = EV × 10%，这些假设不专业

### 1.2 目标架构

```
新数据流：
  ┌─────────────────────────────────────────────────┐
  │                  Data Layer                       │
  │  FMP + yfinance + EDGAR(新) + Industry(新)        │
  │       ↓                                          │
  │  data_cache.py(新)  ←  缓存所有 API 调用          │
  └──────────────────────┬──────────────────────────┘
                         ↓
  ┌─────────────────────────────────────────────────┐
  │              Processing Layer                     │
  │  financial_data_processor.py  →  扩展指标提取      │
  │  valuation_engine.py         →  WACC 自动校准     │
  │  industry_data.py(新)        →  行业数据获取       │
  │  technical_analyzer.py(新)   →  技术信号计算       │
  └──────────────────────┬──────────────────────────┘
                         ↓
  ┌─────────────────────────────────────────────────┐
  │               Agent Layer (重构)                  │
  │  每个模块一个 Agent，接收专属结构化数据             │
  │                                                   │
  │  Agent 1:  投资概要 (InvestmentThesisAgent)        │
  │  Agent 2:  投资逻辑 (InvestmentRationaleAgent)      │
  │  Agent 3:  行业分析 (IndustryAnalysisAgent)   ←新  │
  │  Agent 4:  公司分析 (CompanyAnalysisAgent)         │
  │  Agent 5:  财务分析 (FinancialAnalysisAgent)       │
  │  Agent 6:  盈利预测 (EarningsForecastAgent)        │
  │  Agent 7:  估值分析 (ValuationAnalysisAgent)       │
  │  Agent 8:  技术面   (TechnicalAnalysisAgent)  ←新  │
  │  Agent 9:  关注信号 (MonitorSignalsAgent)     ←新  │
  │  Agent 10: 风险提示 (RiskDisclosureAgent)          │
  │  Agent E:  总编     (EditorAgent)             ←新  │
  └──────────────────────┬──────────────────────────┘
                         ↓
  ┌─────────────────────────────────────────────────┐
  │              Quality Layer (新)                   │
  │  consistency_checker.py  →  数字一致性校验         │
  │  completeness_checker.py →  模块完整性检查         │
  └──────────────────────┬──────────────────────────┘
                         ↓
                    HTML / PDF
```

---

## 二、Week 1-2：数据层增强 + Agent 系统重构

### 2.1 数据层增强（3 天）

#### 2.1.1 新建 `src/core/src/modules/data_cache.py`

**目的**：缓存所有 API 调用结果，避免重复请求消耗额度。

**实现方案**：

```python
# 文件：src/core/src/modules/data_cache.py
# 职责：
# - SQLite 缓存，按 ticker:data_type:fiscal_year:quarter 索引
# - TTL 策略：财报数据缓存 24h，实时行情缓存 5min，行业数据缓存 7d
# - 两个核心函数：cache_get(key) / cache_set(key, data, ttl)
# - 自动检测财报更新（如果已缓存年份 < FMP 可获取年份，则刷新）

import sqlite3
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Any

class DataCache:
    def __init__(self, db_path: str = None):
        # 默认位置：src/core/output/cache.db
        ...
    
    def get(self, cache_key: str) -> Optional[Any]:
        """获取缓存数据，自动检查 TTL"""
        ...
    
    def set(self, cache_key: str, data: Any, ttl_seconds: int = 86400):
        """写入缓存"""
        ...
    
    def invalidate_ticker(self, ticker: str):
        """财报更新时，清除该 ticker 所有缓存"""
        ...

# 全局单例
_cache_instance = None
def get_cache() -> DataCache:
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DataCache()
    return _cache_instance
```

**TTL 策略**：

| 数据类型 | TTL | 原因 |
|---------|-----|------|
| 财务报表 (10-K/10-Q) | 24h | 财报季可能更新 |
| 实时行情 (price/volume) | 5min | 准实时 |
| 公司概况 (profile/sector) | 24h | 基本不变 |
| 行业数据 (market size/growth) | 7d | 变化极慢 |
| 分析师评级 | 24h | 可能有更新 |
| 技术指标 | 1h | 收盘后重算 |

#### 2.1.2 新建 `src/core/src/modules/industry_data.py`

**目的**：为模块三（行业分析）提供数据支撑。

**实现方案**：

```python
# 文件：src/core/src/modules/industry_data.py
# 职责：
# 1. 维护 GICS 行业分类映射表（sector → industry → sub-industry）
# 2. 从 FMP API 获取行业数据（如有）
# 3. 提供行业基本信息（市场规模、增速、集中度等）的静态参考数据
# 4. 根据 ticker 自动确定行业分类

# GICS 一级行业 → 二级行业组 映射（硬编码，权威来源）
GICS_SECTOR_MAP = {
    "Technology": {
        "industries": ["Software", "Hardware", "Semiconductors", "IT Services"],
        "typical_growth_rate": 0.10,
        "typical_ebitda_margin": 0.25,
    },
    "Financial Services": {
        "industries": ["Banks", "Insurance", "Capital Markets", "Consumer Finance"],
        ...
    },
    # ... 共 11 个 GICS 一级行业
}

def get_industry_profile(ticker: str, sector: str, api_key: str = None) -> dict:
    """
    返回该股票所在行业的分析所需数据：
    - industry_name, sector_name
    - market_size_global (估算)
    - market_growth_rate (行业 CAGR)
    - concentration_cr3, concentration_cr5 (集中度)
    - lifecycle_stage (导入期/成长期/成熟期/衰退期)
    - key_trends (3-5 个关键趋势)
    - porter_five_forces (五力评估)
    - key_operating_metrics (该行业的关键运营指标名称)
    """
    ...

def get_peer_tickers_auto(ticker: str, sector: str, market_cap: float, api_key: str) -> list[str]:
    """
    自动筛选可比公司：
    1. 同 GICS Sub-Industry
    2. 市值在 0.3x - 3x 范围内
    3. 排除自身
    4. 按市值最接近的取前 5 个
    """
    ...
```

**数据来源策略**：

- 行业分类：FMP `/profile` 返回 sector/industry → 映射到 GICS
- 市场规模/增速：优先 FMP（如有行业 endpoint），否则使用静态参考数据（来自公开行业报告，标注为"估算"）
- 竞争格局：根据 industry 从静态数据库取 CR3/CR5 估算值
- 可比公司：FMP `/stock-screener` 按 sector + marketCap 范围筛选

#### 2.1.3 扩展 `market_data_api.py` — 增加 EDGAR 数据获取

**修改文件**：`src/core/src/modules/market_data_api.py`

**新增函数**（追加到文件末尾）：

```python
def get_sec_filing_data(ticker: str, filing_type: str = "10-K", limit: int = 3) -> dict:
    """
    从 SEC EDGAR 获取关键披露数据。
    
    使用 python-edgar 库或直接 HTTP 请求 SEC API。
    
    Returns:
        {
            "business_description": str,      # Item 1: Business
            "risk_factors": list[str],        # Item 1A: Risk Factors (前5个)
            "management_discussion": str,      # Item 7: MD&A
            "properties": str,                # Item 2: Properties
            "legal_proceedings": str,         # Item 3: Legal Proceedings
            "filing_date": str,
            "fiscal_year": int,
        }
    """
    ...

def get_insider_transactions(ticker: str, api_key: str, limit: int = 20) -> list[dict]:
    """
    获取内部人交易数据（FMP API 已有此 endpoint）。
    用于管理层分析模块。
    """
    ...

def get_institutional_holdings(ticker: str, api_key: str) -> list[dict]:
    """
    获取机构持仓数据（FMP API 已有此 endpoint）。
    返回前 10 大机构持仓。
    """
    ...
```

#### 2.1.4 修改 `financial_data_processor.py` — 扩展指标提取

**修改文件**：`src/core/src/modules/financial_data_processor.py`

**变更内容**：

1. `extract_historical_metrics_from_api_data()` 扩展输出指标列表，追加：

```python
output_metrics_order = [
    'Revenue', 'Cost of Operations', 'SG&A',
    'Contribution Profit', 'Contribution Margin',
    'EBITDA', 'EBITDA Margin', 'SG&A Margin',
    'Revenue Growth', 'EPS', 'PE Ratio',
    # 新增
    'Net Income',           # 净利润
    'Gross Profit',         # 毛利
    'Operating Income',     # 营业利润
    'Free Cash Flow',       # 自由现金流
    'Total Assets',         # 总资产
    'Total Liabilities',    # 总负债
    'Total Equity',         # 总权益
    'ROE',                  # 净资产收益率
    'ROA',                  # 总资产收益率
    'Net Debt / EBITDA',    # 净负债/EBITDA
    'Current Ratio',        # 流动比率
    'Debt / Equity',        # 负债权益比
]
```

2. 新增函数 `extract_balance_sheet_metrics()` 从 balance_sheet 提取偿债能力指标
3. 新增函数 `extract_cash_flow_metrics()` 从 cash_flow 提取现金流指标
4. 新增函数 `calculate_dupont_analysis()` 计算杜邦分析三因子拆解

---

### 2.2 Agent 系统重构（5 天）

这是 Phase 1 最核心的改造。

#### 2.2.1 设计决策：统一到 OpenAI Agents SDK

**决策**：废弃 `text_generator_agents.py` 的简单 prompt 方式，统一使用 `equity_agents/` 下的 OpenAI Agents SDK 架构。

**原因**：
- Agents SDK 支持结构化输出（Pydantic model 约束 response 格式）
- 支持 `instructions` 和 `model_settings` 分离管理
- 已有框架代码，减少重构量
- 未来可以升级到多 agent 协作模式

#### 2.2.2 新建 Agent 目录结构

```
src/core/src/modules/equity_agents/
├── __init__.py              # 保留，更新导出
├── base.py                  # [新] Agent 基类
├── agent_manager.py         # [重写] 新的编排器
│
├── investment_thesis.py     # [新] Agent 1: 投资概要
├── investment_rationale.py  # [新] Agent 2: 投资逻辑
├── industry_analysis.py     # [新] Agent 3: 行业分析
├── company_analysis.py      # [重写] Agent 4: 公司分析（原 company_overview_agent）
├── financial_analysis.py    # [新] Agent 5: 财务分析
├── earnings_forecast.py     # [新] Agent 6: 盈利预测
├── valuation_analysis.py    # [重写] Agent 7: 估值分析（原 valuation_overview_agent）
├── technical_analysis.py    # [新] Agent 8: 技术面分析
├── monitor_signals.py       # [新] Agent 9: 关注信号
├── risk_disclosure.py       # [重写] Agent 10: 风险提示（原 risks_agent）
├── editor.py                # [新] Agent E: 总编
│
├── tagline_agent.py         # [废弃] 合并入 investment_thesis.py
├── company_overview_agent.py # [废弃] 合并入 company_analysis.py
├── investment_overview_agent.py # [废弃] 合并入 investment_rationale.py
├── valuation_overview_agent.py # [废弃] 合并入 valuation_analysis.py
├── risks_agent.py           # [废弃] 合并入 risk_disclosure.py
├── competitor_analysis_agent.py # [废弃] 合并入 industry_analysis.py + company_analysis.py
├── major_takeaways_agent.py  # [废弃] 合并入 financial_analysis.py
└── news_summary_agent.py     # [保留] 新闻摘要（轻量级，保持独立）
```

**重要**：废弃的文件不删除，保留在目录中，但从 `__init__.py` 移除导出。新建的 Agent 文件名使用下划线，原文件名保留作为参考。

#### 2.2.3 新建 `base.py` — Agent 基类

```python
# 文件：src/core/src/modules/equity_agents/base.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from agents import Agent, ModelSettings

@dataclass
class ModuleData:
    """
    每个模块 Agent 接收的数据包。
    不同模块接收不同的数据子集。
    """
    # 基本信息（所有模块都有）
    company_name: str
    company_ticker: str
    sector: str = ""
    industry: str = ""
    
    # 财务数据（模块 1/2/5/6/7 使用）
    financial_metrics: Optional[dict] = None  # DataFrame → dict
    forecast_data: Optional[dict] = None
    
    # 估值数据（模块 1/7 使用）
    valuation_results: Optional[dict] = None
    
    # 行业数据（模块 2/3 使用）
    industry_data: Optional[dict] = None
    
    # 公司数据（模块 4 使用）
    company_data: Optional[dict] = None  # profile, management, EDGAR
    
    # 技术数据（模块 8 使用）
    technical_data: Optional[dict] = None
    
    # 风险/催化剂数据（模块 2/9/10 使用）
    risk_data: Optional[dict] = None
    catalyst_data: Optional[dict] = None
    
    # 新闻/情绪数据（模块 4/10 使用）
    news_data: Optional[list] = None
    sentiment_data: Optional[dict] = None
    
    # 同行数据（模块 3/7 使用）
    peer_data: Optional[dict] = None


def build_agent(
    name: str,
    instructions: str,
    output_type: type,           # Pydantic BaseModel — 结构化输出约束
    model: str = None,
    temperature: float = 0.3,    # 研报要精确，不宜温度过高
    max_tokens: int = 2000,
) -> Agent:
    """工厂函数，创建标准配置的 Agent"""
    return Agent(
        name=name,
        instructions=instructions,
        output_type=output_type,
        model=model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        model_settings=ModelSettings(
            temperature=temperature,
            max_tokens=max_tokens,
        ),
    )
```

#### 2.2.4 每个 Agent 的设计规范

以 **Agent 3: 行业分析** 为例，展示完整设计：

```python
# 文件：src/core/src/modules/equity_agents/industry_analysis.py

from pydantic import BaseModel, Field
from .base import build_agent, ModuleData

# ============================================================
# 1. 结构化输出定义 — 这是最关键的提升
# ============================================================

class IndustryOverview(BaseModel):
    """行业概览"""
    industry_name: str = Field(..., description="行业名称")
    market_size_usd_bn: str = Field(..., description="全球市场规模（十亿美元）")
    market_size_china_bn: str = Field(..., description="中国市场/相关市场规模（如适用）")
    historical_cagr_3yr: str = Field(..., description="过去3年行业复合增速（如 +8.5%）")
    forecast_cagr_3yr: str = Field(..., description="未来3年行业预期复合增速")
    lifecycle_stage: str = Field(..., description="行业生命周期：导入期/成长期/成熟期/衰退期")
    lifecycle_rationale: str = Field(..., description="生命周期判断依据（1-2句）")

class CompetitivePosition(BaseModel):
    """竞争格局"""
    cr3: str = Field(..., description="CR3 集中度")
    cr5: str = Field(..., description="CR5 集中度")
    company_rank: str = Field(..., description="目标公司在行业中的排名（如 第2位）")
    company_market_share: str = Field(..., description="目标公司市场份额（如 ~15%）")
    competition_intensity: str = Field(..., description="竞争强度：高/中/低")
    key_competitors: str = Field(..., description="3-5个主要竞争对手，逗号分隔")

class PorterFiveForces(BaseModel):
    """波特五力"""
    threat_new_entrants: str = Field(..., description="新进入者威胁：高/中/低 + 1句理由")
    supplier_power: str = Field(..., description="供应商议价能力：高/中/低 + 1句理由")
    buyer_power: str = Field(..., description="买方议价能力：高/中/低 + 1句理由")
    threat_substitutes: str = Field(..., description="替代品威胁：高/中/低 + 1句理由")
    rivalry: str = Field(..., description="现有竞争：高/中/低 + 1句理由")

class IndustryTrend(BaseModel):
    """行业趋势"""
    trend_name: str = Field(..., description="趋势名称")
    description: str = Field(..., description="趋势描述")
    drivers: str = Field(..., description="驱动因素")
    impact_on_company: str = Field(..., description="对公司的影响：正面/负面/中性 + 说明")
    timeline: str = Field(..., description="时间线：短期(1-2年)/中期(3-5年)/长期(5年+)")

class IndustryAnalysisOutput(BaseModel):
    """行业分析模块输出"""
    industry_overview: IndustryOverview
    competitive_position: CompetitivePosition
    porter_five_forces: PorterFiveForces
    trends: list[IndustryTrend] = Field(..., min_items=3, max_items=5)
    key_takeaway: str = Field(..., description="行业分析核心结论（3-5句）")

# ============================================================
# 2. Instructions — 结构化、数据驱动
# ============================================================

INDUSTRY_ANALYSIS_INSTRUCTIONS = """
You are a senior equity research analyst specializing in industry analysis.
Your task is to write the Industry Analysis section of an initiating coverage report.

## Data Provided
You will receive:
- Industry data: market size, growth rates, concentration metrics, lifecycle assessment
- Peer data: key competitors with financial metrics
- Company data: sector, industry classification, market cap, revenue

## Output Requirements
1. EVERY conclusion must reference at least one specific number from the provided data
2. Use precise figures, not vague descriptions ("~$50B" not "large market")
3. For metrics where data is not provided, mark as "Est." and provide a reasoned estimate
4. Porter's Five Forces: each force must include an intensity rating AND a specific reason
5. Trends: must include timeline and quantified impact where possible

## Quality Checklist (self-verify before outputting)
- [ ] Market size includes both global and relevant regional figures
- [ ] Growth rates are labeled as historical (A) or forecast (E)
- [ ] Competitive position includes the company's rank AND market share
- [ ] At least 3 trends with specific drivers and timelines
- [ ] No vague language like "large", "significant", "competitive" without numbers
- [ ] Key takeaway synthesizes the most important investment-relevant insight

## Style
- Professional, data-driven, objective
- Output language: naturally mix English financial terms with the requested output language
"""

# ============================================================
# 3. 数据准备函数 — 只给 Agent 它需要的
# ============================================================

def _prepare_industry_prompt(data: ModuleData) -> str:
    """构建行业分析 Agent 的输入数据摘要"""
    
    lines = []
    lines.append(f"## Company Context")
    lines.append(f"Company: {data.company_name} ({data.company_ticker})")
    lines.append(f"Sector: {data.sector}")
    lines.append(f"Industry: {data.industry}")
    
    if data.industry_data:
        ind = data.industry_data
        lines.append(f"\n## Industry Data")
        lines.append(f"Industry Name: {ind.get('industry_name', 'N/A')}")
        lines.append(f"Global Market Size: ${ind.get('market_size_global_bn', 'N/A')}B")
        lines.append(f"Historical CAGR (3yr): {ind.get('historical_cagr', 'N/A')}%")
        lines.append(f"Forecast CAGR (3yr): {ind.get('forecast_cagr', 'N/A')}%")
        lines.append(f"Lifecycle Stage: {ind.get('lifecycle_stage', 'N/A')}")
        lines.append(f"CR3: {ind.get('cr3', 'N/A')} | CR5: {ind.get('cr5', 'N/A')}")
        lines.append(f"Key Trends Identified: {ind.get('key_trends', [])}")
        lines.append(f"Porter Five Forces (preliminary): {ind.get('porter_five', {})}")
    
    if data.peer_data:
        lines.append(f"\n## Peer Financial Data (Latest Year)")
        for ticker, metrics in data.peer_data.items():
            lines.append(f"- {ticker}: Revenue=${metrics.get('revenue','N/A')}B, "
                        f"Growth={metrics.get('growth','N/A')}%, "
                        f"EBITDA Margin={metrics.get('ebitda_margin','N/A')}%, "
                        f"Market Cap=${metrics.get('market_cap','N/A')}B")
    
    if data.company_data:
        cd = data.company_data
        lines.append(f"\n## Target Company Metrics")
        lines.append(f"Revenue: ${cd.get('revenue', 'N/A')}B")
        lines.append(f"Market Cap: ${cd.get('market_cap', 'N/A')}B")
        lines.append(f"Employees: {cd.get('employees', 'N/A')}")
    
    return "\n".join(lines)


# ============================================================
# 4. Agent 实例创建
# ============================================================

industry_analysis_agent = build_agent(
    name="IndustryAnalysisAgent",
    instructions=INDUSTRY_ANALYSIS_INSTRUCTIONS,
    output_type=IndustryAnalysisOutput,
    temperature=0.3,
    max_tokens=2500,
)
```

#### 2.2.5 10 个 Agent 的输出结构定义

每个 Agent 的输出 Pydantic model 必须与 `equity_research_template.md` 中定义的模块内容严格对应。

| Agent | Pydantic Output 类 | 核心字段 | 数据依赖 |
|-------|-------------------|---------|---------|
| Agent 1: InvestmentThesis | `InvestmentThesisOutput` | rating, target_price, current_price, market_cap, 52w_range, core_theses[], financial_snapshot | 所有模块数据摘要 |
| Agent 2: InvestmentRationale | `InvestmentRationaleOutput` | pillars[] (每个含 market_opportunity, competitive_advantage, financial_impact), risk_symmetry | industry_data, financial_metrics, risk_data |
| Agent 3: IndustryAnalysis | `IndustryAnalysisOutput` | industry_overview, competitive_position, porter_five_forces, trends[] | industry_data, peer_data |
| Agent 4: CompanyAnalysis | `CompanyAnalysisOutput` | business_model, management[], business_segments[], moat_analysis, growth_drivers[], customer_analysis | company_data, edgar_data, news_data |
| Agent 5: FinancialAnalysis | `FinancialAnalysisOutput` | revenue_analysis, profitability_analysis, dupont_analysis, cashflow_analysis, credit_analysis, operating_metrics[] | financial_metrics (完整) |
| Agent 6: EarningsForecast | `EarningsForecastOutput` | assumptions[], forecast_income_statement, scenarios[] (bull/base/bear) | forecast_data, industry_data |
| Agent 7: ValuationAnalysis | `ValuationAnalysisOutput` | dcf_result, peer_comparison[], historical_range[], football_field, final_rating | valuation_results, peer_data |
| Agent 8: TechnicalAnalysis | `TechnicalAnalysisOutput` | trend_assessment, key_levels[], momentum_signals[], summary | technical_data |
| Agent 9: MonitorSignals | `MonitorSignalsOutput` | signals[] (每个含 name, method, positive_signal, negative_signal) | catalyst_data, risk_data, forecast_data |
| Agent 10: RiskDisclosure | `RiskDisclosureOutput` | macro_risks[], industry_risks[], operational_risks[], valuation_risks[], risk_summary | risk_data, industry_data, valuation_results |
| Agent E: Editor | `EditorOutput` | executive_summary, style_fixes[], consistency_issues[], final_tagline | 所有 10 个 Agent 的输出 |

#### 2.2.6 重写 `agent_manager.py` — 新的编排器

```python
# 文件：src/core/src/modules/equity_agents/agent_manager.py (重写)

import asyncio
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from agents import Runner, RunConfig, ModelSettings

from .base import ModuleData
from .investment_thesis import investment_thesis_agent
from .investment_rationale import investment_rationale_agent
from .industry_analysis import industry_analysis_agent
from .company_analysis import company_analysis_agent
from .financial_analysis import financial_analysis_agent
from .earnings_forecast import earnings_forecast_agent
from .valuation_analysis import valuation_analysis_agent
from .technical_analysis import technical_analysis_agent
from .monitor_signals import monitor_signals_agent
from .risk_disclosure import risk_disclosure_agent
from .editor import editor_agent


class EquityResearchAgentManager:
    """重构后的 Agent 编排器"""
    
    def __init__(self, model: str = None):
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.agents = {
            "investment_thesis": investment_thesis_agent,
            "investment_rationale": investment_rationale_agent,
            "industry_analysis": industry_analysis_agent,
            "company_analysis": company_analysis_agent,
            "financial_analysis": financial_analysis_agent,
            "earnings_forecast": earnings_forecast_agent,
            "valuation_analysis": valuation_analysis_agent,
            "technical_analysis": technical_analysis_agent,
            "monitor_signals": monitor_signals_agent,
            "risk_disclosure": risk_disclosure_agent,
        }
    
    async def generate_module(self, module_name: str, data: ModuleData) -> dict:
        """
        运行单个模块 Agent（异步）。
        
        Returns:
            Agent 输出的 dict（Pydantic model → dict）
        """
        if module_name not in self.agents:
            raise ValueError(f"Unknown module: {module_name}")
        
        agent = self.agents[module_name]
        prompt = data.to_prompt(module_name)  # ModuleData 知道如何为每个模块生成 prompt
        
        result = await Runner.run(agent, prompt)
        return result.final_output.model_dump()
    
    async def generate_all_modules(self, data: ModuleData) -> Dict[str, dict]:
        """
        并行运行所有模块 Agent（独立模块可以并行）。
        
        执行顺序：
        Phase 1 (并行):
          - industry_analysis, company_analysis, financial_analysis
          - earnings_forecast, valuation_analysis, technical_analysis
        
        Phase 2 (依赖 Phase 1):
          - investment_rationale (依赖 industry + financial)
          - risk_disclosure (依赖 industry + valuation)
          - monitor_signals (依赖 risk + earnings)
        
        Phase 3 (依赖所有):
          - investment_thesis (依赖所有)
          - editor (依赖所有)
        """
        results = {}
        
        # Phase 1: 独立模块并行执行
        phase1_modules = [
            "industry_analysis",
            "company_analysis",
            "financial_analysis",
            "earnings_forecast",
            "valuation_analysis",
            "technical_analysis",
        ]
        phase1_tasks = [self.generate_module(m, data) for m in phase1_modules]
        phase1_results = await asyncio.gather(*phase1_tasks, return_exceptions=True)
        for name, result in zip(phase1_modules, phase1_results):
            if isinstance(result, Exception):
                print(f"Error in {name}: {result}")
                results[name] = {"error": str(result)}
            else:
                results[name] = result
        
        # Phase 2: 依赖模块（串行，但可以考虑并行如果数据够）
        for module in ["investment_rationale", "risk_disclosure", "monitor_signals"]:
            try:
                results[module] = await self.generate_module(module, data)
            except Exception as e:
                print(f"Error in {module}: {e}")
                results[module] = {"error": str(e)}
        
        # Phase 3: 汇总模块
        data.module_results = results  # 注入所有模块结果
        for module in ["investment_thesis", "editor"]:
            try:
                results[module] = await self.generate_module(module, data)
            except Exception as e:
                print(f"Error in {module}: {e}")
                results[module] = {"error": str(e)}
        
        return results
```

#### 2.2.7 修改 `generate_financial_analysis.py` — 集成新 Agent 系统

**修改文件**：`src/core/src/generate_financial_analysis.py`

**关键变更**：

1. 第 9 行导入改为：

```python
# 旧
from modules.text_generator_agents import generate_text_section

# 新
from modules.equity_agents import EquityResearchAgentManager
from modules.equity_agents.base import ModuleData
from modules.industry_data import get_industry_profile, get_peer_tickers_auto
from modules.data_cache import get_cache
```

2. 第 395-473 行的文本生成部分重写为：

```python
if args.generate_text_sections:
    print("\nGenerating AI-powered text sections with structured agent system...")
    
    if 'openai_api_key' not in locals() or not openai_api_key:
        print("Error: OpenAI API key not loaded. Skipping text generation.")
    else:
        # 获取行业数据
        print("Fetching industry data...")
        sector = auto_fetched_sector  # 从 FMP profile 获取
        industry_data = get_industry_profile(args.company_ticker, sector, fmp_api_key)
        
        # 自动筛选可比公司
        print("Auto-selecting peer companies...")
        auto_peers = get_peer_tickers_auto(
            args.company_ticker, sector, market_cap, fmp_api_key
        )
        
        # 构建 ModuleData
        module_data = ModuleData(
            company_name=args.company_name,
            company_ticker=args.company_ticker,
            sector=sector,
            financial_metrics=final_data_df.to_dict(),
            forecast_data=forecast_dict,
            industry_data=industry_data,
            company_data=company_data_dict,
            technical_data=technical_indicators,
            peer_data=peer_metrics_dict,
            risk_data=risk_data_dict,
            catalyst_data=catalyst_results,
            news_data=company_news,
            valuation_results=valuation_results,
        )
        
        # 启动 Agent 系统
        manager = EquityResearchAgentManager(model=openai_model)
        
        # 异步运行所有 Agent
        import asyncio
        all_results = asyncio.run(manager.generate_all_modules(module_data))
        
        # 保存结果
        for module_name, result in all_results.items():
            file_path = os.path.join(text_output_dir, f"{module_name}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Saved {module_name} to {file_path}")
        
        # 同时保存纯文本版本（向后兼容 create_equity_report.py）
        for module_name, result in all_results.items():
            text = _extract_text_from_agent_output(module_name, result)
            file_path = os.path.join(text_output_dir, f"{module_name}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
```

---

### 2.3 估值模型升级（2 天）

#### 2.3.1 重写 `valuation_engine.py` 中的 DCF 模型

**修改文件**：`src/core/src/modules/valuation_engine.py`

**关键变更**：

1. WACC 自动计算：

```python
def calculate_wacc(
    self,
    risk_free_rate: float = None,    # 10Y Treasury yield（自动获取）
    beta: float = None,               # 5Y monthly regression vs S&P500
    market_risk_premium: float = 0.055,  # 默认 5.5%
    cost_of_debt: float = None,
    tax_rate: float = 0.21,
    debt_weight: float = None,
    equity_weight: float = None,
) -> float:
    """
    根据 CAPM 模型自动计算 WACC。
    
    优先从 FMP 获取 beta，否则从 yfinance 计算。
    无风险利率默认从 FMP 获取最新 10Y Treasury。
    """
    if risk_free_rate is None:
        risk_free_rate = self._get_risk_free_rate()  # 新增辅助方法
    if beta is None:
        beta = self._get_beta() or 1.0
    if debt_weight is None:
        debt_weight = self._get_debt_weight()
    equity_weight = 1 - debt_weight
    
    cost_of_equity = risk_free_rate + beta * market_risk_premium
    
    if cost_of_debt is None:
        cost_of_debt = risk_free_rate + 0.02  # 简化：国债 + 2% 信用利差
    
    wacc = equity_weight * cost_of_equity + debt_weight * cost_of_debt * (1 - tax_rate)
    return wacc
```

2. 历史估值分位计算：

```python
def calculate_historical_percentile(
    self,
    ticker: str,
    metrics: list = ['PE', 'PB', 'EV/EBITDA']
) -> dict:
    """
    获取 1年/3年/5年 的估值分位数。
    
    Returns:
        {
            "PE": {
                "current": 28.5,
                "percentile_1y": 65,  # 高于过去1年65%的时间
                "percentile_3y": 72,
                "percentile_5y": 58,
                "historical_median_5y": 25.3,
                "historical_range_5y": [15.2, 38.7]
            },
            ...
        }
    """
```

3. Football Field 图表数据增强：

```python
def generate_football_field_data(self) -> dict:
    """
    扩展版 Football Field 数据，包含：
    - DCF 估值区间（Bull/Base/Bear）
    - PE 估值区间（Forward PE × Bull/Base/Bear EPS）
    - PB 估值区间
    - EV/EBITDA 估值区间
    - 52 周价格区间
    - 分析师目标价区间
    - 当前股价
    """
```

4. 评级自动推导：

```python
def derive_rating(self, current_price: float, target_price: float) -> dict:
    """
    基于目标价和现价的偏离自动推导评级：
    
    upside >= 20%   → Buy
    upside 10-20%   → Overweight
    upside -5-10%   → Neutral
    upside -20--5%  → Underweight
    upside < -20%   → Sell
    """
```

#### 2.3.2 修改 `sensitivity_analyzer.py` — 三情景自动化

**修改文件**：`src/core/src/modules/sensitivity_analyzer.py`

**新增函数**：

```python
def generate_three_scenarios(self) -> dict:
    """
    基于历史波动率自动生成三情景预测：
    
    - 乐观（Bull）：营收增速 = base + 1 std，利润率 +50bp
    - 基准（Base）：当前预测
    - 悲观（Bear）：营收增速 = base - 1 std，利润率 -50bp
    
    每个情景包含：revenue, eps, target_price, 概率
    """
```

---

## 三、Week 3：补全缺失模块 + 估值模型升级

### 3.1 行业分析模块实现（1.5 天）

**依赖**：`industry_data.py` 完成（Week 1-2 产出）

**任务**：
1. 实现 `industry_analysis.py` Agent（已在 2.2.4 设计了完整规范）
2. 实现 `_prepare_industry_prompt()` 数据准备函数
3. 连接到 `agent_manager.py` 的 Phase 1 并行执行

### 3.2 技术面分析模块（1.5 天）

**文件**：`src/core/src/modules/equity_agents/technical_analysis.py`

**输出结构**：

```python
class TrendAssessment(BaseModel):
    ma_arrangement: str  # "多头排列" / "空头排列" / "交叉震荡"
    ma5: str
    ma20: str
    ma60: str
    ma120: str
    price_vs_ma200: str  # "上方 +X%" / "下方 -X%"

class KeyLevel(BaseModel):
    level_type: str    # "强支撑" / "弱支撑" / "弱压力" / "强压力"
    price: str
    basis: str         # 依据

class MomentumSignal(BaseModel):
    rsi14: str
    rsi_signal: str    # "超买(>70)" / "中性(30-70)" / "超卖(<30)"
    macd_signal: str   # "金叉" / "死叉" / "零轴上方" / "零轴下方"
    volume_signal: str # "放量" / "缩量" / "正常"
    change_20d: str
    change_60d: str

class TechnicalAnalysisOutput(BaseModel):
    trend_assessment: TrendAssessment
    key_levels: list[KeyLevel]  # 4 个关键价位
    momentum_signals: MomentumSignal
    summary: str  # 一句话趋势定性
    bullish_condition: str  # 什么条件成立才确认趋势转好
    bearish_condition: str  # 什么条件成立需降低关注
```

**数据依赖**：`get_technical_indicators()` 已在 `market_data_api.py` 中实现，直接复用。

### 3.3 后续关注信号模块（1 天）

**文件**：`src/core/src/modules/equity_agents/monitor_signals.py`

**输出结构**：

```python
class MonitorSignal(BaseModel):
    rank: int
    signal_name: str        # 如 "下季度营收增速"
    observation_method: str  # 如 "关注Q1 FY2027财报"
    positive_signal: str    # 如 "增速 > 8% 则投资逻辑确认"
    negative_signal: str    # 如 "增速 < 3% 则需重新评估"
    current_status: str     # 当前状态描述

class MonitorSignalsOutput(BaseModel):
    signals: list[MonitorSignal]  # 3-5 个
```

**生成逻辑**：从 catalyst_data、risk_data、forecast_data 中找到关键假设，为每个关键假设生成一个跟踪信号。

### 3.4 总编 Agent（0.5 天）

**文件**：`src/core/src/modules/equity_agents/editor.py`

**职责**：

```python
class EditorOutput(BaseModel):
    executive_summary: str          # 300-400 字执行摘要
    tagline: str                    # 3 句投资标语
    style_issues: list[str]         # 发现的风格不一致问题
    consistency_issues: list[str]   # 发现的数据/逻辑矛盾
    final_rating: str               # 确认最终评级
    final_target_price: str         # 确认最终目标价
```

---

## 四、Week 4：质量保障 + 评测基准

### 4.1 一致性校验器（1.5 天）

**文件**：`src/core/src/modules/consistency_checker.py`（新建）

```python
class ConsistencyChecker:
    """报告一致性校验"""
    
    def check_numeric_consistency(self, module_results: dict, source_data: dict) -> list[str]:
        """
        校验 Agent 生成文本中引用的数字是否与源数据一致。
        
        方法：用正则提取 Agent 输出中的数字 → 与 source_data 中的原始值比对
        """
        ...
    
    def check_cross_module_consistency(self, module_results: dict) -> list[str]:
        """
        检查不同模块之间的数据是否自洽。
        例如：估值模块引用的 PE 是否与财务模块中的 PE 一致
        """
        ...
    
    def check_rating_consistency(self, module_results: dict) -> list[str]:
        """
        检查评级逻辑是否自洽：
        - 目标价 > 现价 → 评级应该是买入/增持
        - 风险提示中不应该有"前景非常好"这种与风险分析矛盾的表述
        """
        ...
```

### 4.2 完整性检查器（1 天）

**文件**：`src/core/src/modules/completeness_checker.py`（新建）

```python
class CompletenessChecker:
    """报告完整性检查"""
    
    REQUIRED_MODULES = [
        "investment_thesis", "investment_rationale", "industry_analysis",
        "company_analysis", "financial_analysis", "earnings_forecast",
        "valuation_analysis", "technical_analysis", "monitor_signals",
        "risk_disclosure",
    ]
    
    def check_all(self, module_results: dict) -> dict:
        """
        检查项：
        1. 10 个模块是否全部有输出（非空、非 error）
        2. 每个模块的关键字段是否不为空
        3. 财务快照表是否包含所有必需指标
        4. 风险提示是否覆盖四维
        5. 图表是否全部生成
        6. 数据引用密度（每 100 字至少有几个数字引用）
        """
        ...
```

### 4.3 人工评测基准（1.5 天）

**目的**：建立可复用的质量评测体系，每次代码变更后跑一次。

**评测股票选择**（覆盖不同行业和特征）：

| Ticker | 公司 | 行业 | 测试重点 |
|--------|------|------|---------|
| AAPL | Apple | Technology | 高市值、成长型、全球业务 |
| JPM | JPMorgan Chase | Financial Services | 银行业、受利率影响大 |
| XOM | Exxon Mobil | Energy | 周期股、大宗商品关联 |
| LLY | Eli Lilly | Healthcare | 制药、管线依赖 |
| HD | Home Depot | Consumer Discretionary | 消费周期、宏观敏感 |

**评测流程**：

```
1. 对每只股票生成完整报告
2. 人工逐模块评分（1-10 分）
   评分维度：
   a. 数据准确性 — 引用的数字是否与源数据一致
   b. 分析深度 — 是否有因果分析而非仅描述
   c. 逻辑自洽 — 投资逻辑是否与估值/风险呼应
   d. 可读性 — 结构清晰、语言专业
   e. 完整性 — 所有必需章节是否齐全
3. 记录每个模块的问题和改进建议
4. 汇总得分，作为基线（Baseline）
5. 后续每次 agent prompt 或数据层变更后重跑评测，对比基线
```

**评测工具**：

```python
# 文件：src/core/tests/benchmark.py (新建)

def run_benchmark(tickers: list[str]) -> dict:
    """
    批量生成报告并输出评测清单。
    
    Returns:
        {
            "AAPL": {
                "report_path": "...",
                "module_scores": {"investment_thesis": 7, ...},
                "issues_found": [...],
                "overall_score": 7.2,
            },
            ...
        }
    """
```

---

## 五、文件变更清单

### 新建文件（8 个）

| 文件 | 职责 | 估时 |
|------|------|------|
| `src/core/src/modules/data_cache.py` | API 数据缓存层 | 1d |
| `src/core/src/modules/industry_data.py` | 行业数据获取与分类 | 1d |
| `src/core/src/modules/equity_agents/base.py` | Agent 基类和 ModuleData | 0.5d |
| `src/core/src/modules/equity_agents/investment_thesis.py` | Agent 1: 投资概要 | 0.5d |
| `src/core/src/modules/equity_agents/investment_rationale.py` | Agent 2: 投资逻辑 | 0.5d |
| `src/core/src/modules/equity_agents/industry_analysis.py` | Agent 3: 行业分析 | 0.5d |
| `src/core/src/modules/equity_agents/financial_analysis.py` | Agent 5: 财务分析 | 0.5d |
| `src/core/src/modules/equity_agents/earnings_forecast.py` | Agent 6: 盈利预测 | 0.5d |
| `src/core/src/modules/equity_agents/technical_analysis.py` | Agent 8: 技术面分析 | 0.5d |
| `src/core/src/modules/equity_agents/monitor_signals.py` | Agent 9: 关注信号 | 0.5d |
| `src/core/src/modules/equity_agents/editor.py` | Agent E: 总编 | 0.5d |
| `src/core/src/modules/consistency_checker.py` | 数字一致性校验 | 0.5d |
| `src/core/src/modules/completeness_checker.py` | 报告完整性检查 | 0.5d |
| `src/core/tests/benchmark.py` | 评测基准工具 | 0.5d |

### 重写文件（5 个）

| 文件 | 变更内容 | 估时 |
|------|---------|------|
| `src/core/src/modules/equity_agents/agent_manager.py` | 完全重写：三阶段并行执行 + ModuleData 数据流 | 1d |
| `src/core/src/modules/equity_agents/company_analysis.py` | 重写：增加管理层/业务拆分/护城河分析，结构化输出 | 0.5d |
| `src/core/src/modules/equity_agents/valuation_analysis.py` | 重写：增加 DCF 详述/历史分位/评级推导，结构化输出 | 0.5d |
| `src/core/src/modules/equity_agents/risk_disclosure.py` | 重写：四维风险分类，结构化输出 | 0.5d |
| `src/core/src/modules/equity_agents/__init__.py` | 更新导出，废弃旧 agent | 0.25d |

### 修改文件（4 个）

| 文件 | 变更内容 | 估时 |
|------|---------|------|
| `src/core/src/generate_financial_analysis.py` | 集成新 Agent 系统、行业数据、数据缓存 | 1d |
| `src/core/src/modules/valuation_engine.py` | WACC 自动校准、历史分位、评级推导 | 1d |
| `src/core/src/modules/market_data_api.py` | 增加 EDGAR、内部交易、机构持仓接口 | 1d |
| `src/core/src/modules/financial_data_processor.py` | 扩展指标提取（偿债/现金流/杜邦） | 0.5d |
| `src/core/src/modules/sensitivity_analyzer.py` | 三情景自动生成 | 0.5d |

---

## 六、验收标准

### Phase 1 完成标准

- [ ] 10 个模块 Agent 全部实现，结构化输出定义完整
- [ ] 数据缓存层工作正常，同一 ticker 重复请求使用缓存
- [ ] 行业数据模块可为 AAPL/JPM/XOM 返回正确的行业分类和基本信息
- [ ] WACC 自动从 beta + 无风险利率计算，无需手动传参
- [ ] 可比公司自动筛选结果与行业常识一致（误差在合理范围内）
- [ ] 生成 5 只评测基准股票（AAPL/JPM/XOM/LLY/HD）的完整报告
- [ ] 一致性校验对不同模块之间的数字矛盾至少报告 80% 的问题
- [ ] 人工评测平均分 >= 7.0/10（当前预估约 3.5-4.0）
- [ ] 单份报告生成时间 < 5 分钟（并行 Agent 执行应比当前串行更快）
- [ ] 向后兼容：CLI 命令行接口不变，init 参数保持兼容
- [ ] 旧 `text_generator_agents.py` 仍可独立使用（作为降级方案）

---

## 附录 A：Agent 数据依赖矩阵

| Agent | Fin Metrics | Forecast | Industry | Company | Technical | Valuation | Risk/Catalyst | News | Peer |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| A1 投资概要 | ✓ | ✓ | ✓ | ✓ | - | ✓ | - | - | ✓ |
| A2 投资逻辑 | ✓ | - | ✓ | ✓ | - | - | ✓ | - | ✓ |
| A3 行业分析 | - | - | ✓ | ✓ | - | - | - | - | ✓ |
| A4 公司分析 | - | - | - | ✓ | - | - | - | ✓ | - |
| A5 财务分析 | ✓ | ✓ | - | - | - | - | - | - | - |
| A6 盈利预测 | ✓ | ✓ | ✓ | - | - | - | - | - | - |
| A7 估值分析 | - | ✓ | - | - | - | ✓ | - | - | ✓ |
| A8 技术面 | - | - | - | - | ✓ | - | - | - | - |
| A9 关注信号 | - | ✓ | - | - | - | - | ✓ | - | - |
| A10 风险提示 | - | - | ✓ | ✓ | - | ✓ | ✓ | - | - |
| AE 总编 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

## 附录 B：开发顺序建议

按依赖关系，推荐以下开发顺序：

```
Day 1-2:   data_cache.py → industry_data.py
Day 3:     market_data_api.py 扩展 (EDGAR) + financial_data_processor.py 扩展
Day 4-5:   base.py → 每个 Agent 的 Pydantic 输出类
Day 6-8:   逐个实现 Agent (按 A3→A5→A6→A8→A9→A4→A7→A10→A2→A1→AE 顺序)
Day 9:     agent_manager.py 重写 → generate_financial_analysis.py 集成
Day 10:    valuation_engine.py 升级 + sensitivity_analyzer.py 扩展
Day 11-12: consistency_checker.py + completeness_checker.py
Day 13-14: benchmark.py + 人工评测 + 修 bug + 调 prompt
```

---

> 下一步：确认此方案后，可以按 Day 1 开始实施。建议从 `data_cache.py` 和 `base.py` 开始，这两者独立性最强，是所有后续工作的基础设施。
