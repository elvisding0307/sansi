"""
10-Module Professional HTML Report Renderer (Bilingual: zh/en).

Renders the full 10-module Initiating Coverage report from agent JSON outputs,
following the equity_research_template.md structure.

Usage:
    render_10module_html(agent_outputs, report_meta, language="zh") -> str
"""

import json
import re as _re
from datetime import datetime
from typing import Dict, Any, Optional


# ================================================================
# Bilingual label system
# ================================================================

def T(key: str, lang: str = "zh") -> str:
    """Return the label for the given key in the specified language."""
    return _LABELS.get(key, {}).get(lang, key)

_LABELS: Dict[str, Dict[str, str]] = {
    # Header
    "initiating_coverage": {"zh": "首次覆盖报告", "en": "INITIATING COVERAGE"},
    "rating": {"zh": "评级", "en": "Rating"},
    "price": {"zh": "当前价", "en": "Price"},
    "target_12m": {"zh": "12个月目标价", "en": "12M Target"},
    "market_cap": {"zh": "总市值", "en": "Market Cap"},
    "report_date": {"zh": "报告日期", "en": "Report Date"},
    "sector_label": {"zh": "行业", "en": "Sector"},
    # Modules
    "m1_title": {"zh": "一、投资概要", "en": "1. Investment Thesis"},
    "m2_title": {"zh": "二、投资逻辑与风险", "en": "2. Investment Rationale & Risk"},
    "m3_title": {"zh": "三、行业分析", "en": "3. Industry Analysis"},
    "m4_title": {"zh": "四、公司分析", "en": "4. Company Analysis"},
    "m5_title": {"zh": "五、财务分析", "en": "5. Financial Analysis"},
    "m6_title": {"zh": "六、盈利预测", "en": "6. Earnings Forecast"},
    "m7_title": {"zh": "七、估值分析", "en": "7. Valuation Analysis"},
    "m8_title": {"zh": "八、技术面分析", "en": "8. Technical Analysis"},
    "m9_title": {"zh": "九、后续关注信号", "en": "9. Key Monitor Signals"},
    "m10_title": {"zh": "十、风险提示", "en": "10. Risk Disclosure"},
    "overall_assessment": {"zh": "综合评估", "en": "Overall Assessment"},
    # Module 1
    "rating_box": {"zh": "评级框", "en": "Rating Box"},
    "current_price": {"zh": "最新价", "en": "Current Price"},
    "target_price": {"zh": "目标价", "en": "Target Price"},
    "week_52_range": {"zh": "52周区间", "en": "52-Week Range"},
    "float_market_cap": {"zh": "流通市值", "en": "Float Market Cap"},
    "core_theses": {"zh": "核心投资论点", "en": "Core Investment Theses"},
    "thesis_prefix": {"zh": "论点", "en": "Thesis"},
    "financial_snapshot": {"zh": "财务与估值快照", "en": "Financial & Valuation Snapshot"},
    "executive_summary": {"zh": "执行摘要", "en": "Executive Summary"},
    # Module 2
    "investment_pillars": {"zh": "投资逻辑支柱", "en": "Investment Pillars"},
    "pillar_prefix": {"zh": "支柱", "en": "Pillar"},
    "market_opportunity": {"zh": "市场机会量化", "en": "Market Opportunity"},
    "competitive_advantage": {"zh": "竞争优势", "en": "Competitive Advantage"},
    "financial_impact": {"zh": "财务影响", "en": "Financial Impact"},
    "company_risks": {"zh": "公司特有风险", "en": "Company-Specific Risks"},
    "industry_risks": {"zh": "行业/市场风险", "en": "Industry & Market Risks"},
    # Module 3
    "industry_overview": {"zh": "行业定义与市场规模", "en": "Industry Definition & Market Size"},
    "industry_name": {"zh": "行业名称", "en": "Industry"},
    "industry_boundary": {"zh": "行业边界", "en": "Boundary"},
    "market_size_global": {"zh": "全球市场规模", "en": "Global Market Size"},
    "historical_cagr": {"zh": "历史CAGR", "en": "Historical CAGR"},
    "forecast_cagr": {"zh": "预测CAGR", "en": "Forecast CAGR"},
    "lifecycle_stage": {"zh": "生命周期阶段", "en": "Lifecycle Stage"},
    "industry_chain": {"zh": "产业链分析", "en": "Industry Chain Analysis"},
    "chain_description": {"zh": "产业链描述", "en": "Chain Description"},
    "value_distribution": {"zh": "价值分配", "en": "Value Distribution"},
    "company_position_chain": {"zh": "公司定位与议价能力", "en": "Company Position & Bargaining Power"},
    "competitive_landscape": {"zh": "竞争格局", "en": "Competitive Landscape"},
    "concentration": {"zh": "行业集中度", "en": "Concentration"},
    "competition_intensity": {"zh": "竞争强度", "en": "Intensity"},
    "company_rank": {"zh": "公司排名/份额", "en": "Company Rank/Share"},
    "porter_five": {"zh": "波特五力分析", "en": "Porter's Five Forces"},
    "key_trends": {"zh": "关键行业趋势", "en": "Key Industry Trends"},
    "impact_on_company": {"zh": "对公司的影响", "en": "Impact on Company"},
    # Module 4
    "company_overview": {"zh": "公司概况", "en": "Company Overview"},
    "one_liner": {"zh": "一句话定位", "en": "One-liner"},
    "business_model": {"zh": "商业模式", "en": "Business Model"},
    "customers": {"zh": "目标客群", "en": "Customers"},
    "scale": {"zh": "规模", "en": "Scale"},
    "ownership": {"zh": "股权结构", "en": "Ownership"},
    "milestones": {"zh": "发展历程", "en": "Key Milestones"},
    "management_team": {"zh": "管理层", "en": "Management Team"},
    "governance": {"zh": "治理结构", "en": "Governance"},
    "business_segments": {"zh": "主营业务拆分", "en": "Business Segment Breakdown"},
    "moat_analysis": {"zh": "核心竞争力（护城河）", "en": "Competitive Moat Analysis"},
    "moat_overall": {"zh": "综合护城河评级", "en": "Overall Moat Rating"},
    "growth_drivers": {"zh": "成长驱动", "en": "Growth Drivers"},
    "short_term_drivers": {"zh": "短期驱动（1-2年）", "en": "Short-term (1-2 years)"},
    "medium_term_drivers": {"zh": "中期驱动（3-5年）", "en": "Medium-term (3-5 years)"},
    "customer_analysis": {"zh": "客户与渠道分析", "en": "Customer & Channel Analysis"},
    # Module 5
    "revenue_analysis": {"zh": "收入分析", "en": "Revenue Analysis"},
    "profitability_analysis": {"zh": "盈利能力分析", "en": "Profitability Analysis"},
    "dupont_analysis": {"zh": "杜邦分析", "en": "DuPont Analysis"},
    "operating_efficiency": {"zh": "运营效率", "en": "Operating Efficiency"},
    "cash_flow_analysis": {"zh": "现金流分析", "en": "Cash Flow Analysis"},
    "credit_metrics": {"zh": "偿债能力与资本结构", "en": "Credit & Capital Structure"},
    "industry_kpis": {"zh": "行业特定核心运营指标", "en": "Industry-Specific KPIs"},
    # Module 6
    "core_assumptions": {"zh": "核心假设", "en": "Core Assumptions"},
    "forecast_income_statement": {"zh": "预测损益表", "en": "Forecast Income Statement"},
    "scenario_analysis": {"zh": "情景分析", "en": "Scenario Analysis"},
    # Module 7
    "dcf_valuation": {"zh": "DCF 绝对估值", "en": "DCF Valuation"},
    "peer_comparison": {"zh": "可比公司相对估值", "en": "Peer Comparison"},
    "selection_criteria": {"zh": "可比公司选择标准", "en": "Selection Criteria"},
    "historical_valuation": {"zh": "历史估值区间", "en": "Historical Valuation Range"},
    "valuation_summary": {"zh": "估值汇总（Football Field）", "en": "Valuation Summary (Football Field)"},
    "rating_recommendation": {"zh": "评级与投资建议", "en": "Rating & Recommendation"},
    "suitable_style": {"zh": "适合风格", "en": "Suitable Style"},
    "unsuitable_style": {"zh": "不适合风格", "en": "Unsuitable Style"},
    # Module 8
    "trend_assessment": {"zh": "趋势判断", "en": "Trend Assessment"},
    "key_levels": {"zh": "关键价位", "en": "Key Price Levels"},
    "momentum_volume": {"zh": "动量与量价", "en": "Momentum & Volume"},
    "tech_summary": {"zh": "技术面总结", "en": "Summary"},
    "bullish_trigger": {"zh": "趋势转好条件", "en": "Bullish Trigger"},
    "bearish_trigger": {"zh": "止损/降低关注条件", "en": "Bearish Trigger"},
    # Module 9
    "monitor_signals": {"zh": "关键跟踪信号", "en": "Key Monitor Signals"},
    "monitoring_frequency": {"zh": "建议跟踪频率", "en": "Recommended Monitoring Frequency"},
    # Module 10
    "macro_risks": {"zh": "宏观风险", "en": "Macro Risks"},
    "industry_risks_title": {"zh": "行业风险", "en": "Industry Risks"},
    "operational_risks": {"zh": "经营风险", "en": "Operational Risks"},
    "valuation_risks": {"zh": "估值风险", "en": "Valuation Risks"},
    "risk_reward_summary": {"zh": "风险收益总结", "en": "Risk-Reward Summary"},
    # Table headers
    "th_item": {"zh": "项目", "en": "Item"},
    "th_content": {"zh": "内容", "en": "Content"},
    "th_metric": {"zh": "指标", "en": "Metric"},
    "th_company": {"zh": "公司", "en": "Company"},
    "th_revenue": {"zh": "营收", "en": "Revenue"},
    "th_rev_growth": {"zh": "营收增速", "en": "Rev Growth"},
    "th_gross_margin": {"zh": "毛利率", "en": "Gross Margin"},
    "th_roe": {"zh": "ROE", "en": "ROE"},
    "th_pe": {"zh": "PE", "en": "PE"},
    "th_pb": {"zh": "PB", "en": "PB"},
    "th_market_cap": {"zh": "市值", "en": "Market Cap"},
    "th_parameter": {"zh": "参数", "en": "Parameter"},
    "th_value_2025e": {"zh": "2025E", "en": "2025E"},
    "th_value_2026e": {"zh": "2026E", "en": "2026E"},
    "th_value_2027e": {"zh": "2027E", "en": "2027E"},
    "th_rationale": {"zh": "依据", "en": "Rationale"},
    "th_line_item": {"zh": "项目", "en": "Line Item"},
    "th_method": {"zh": "估值方法", "en": "Method"},
    "th_weight": {"zh": "权重", "en": "Weight"},
    "th_price_range": {"zh": "估值区间", "en": "Price Range"},
    "th_weighted_price": {"zh": "加权价格", "en": "Weighted Price"},
    "th_type": {"zh": "类型", "en": "Type"},
    "th_price": {"zh": "价位", "en": "Price"},
    "th_basis": {"zh": "依据", "en": "Basis"},
    "th_rank": {"zh": "序号", "en": "#"},
    "th_signal": {"zh": "信号", "en": "Signal"},
    "th_observation": {"zh": "观测方法", "en": "Observation Method"},
    "th_positive_signal": {"zh": "正面信号", "en": "Positive Signal"},
    "th_negative_signal": {"zh": "负面信号", "en": "Negative Signal"},
    "th_force": {"zh": "竞争力量", "en": "Force"},
    "th_intensity": {"zh": "强度", "en": "Intensity"},
    "th_analysis": {"zh": "分析", "en": "Analysis"},
    "th_scenario": {"zh": "情景", "en": "Scenario"},
    "th_assumptions": {"zh": "假设条件", "en": "Assumptions"},
    "th_target_price": {"zh": "目标价", "en": "Target Price"},
    "th_probability": {"zh": "概率", "en": "Probability"},
    "th_current": {"zh": "当前值", "en": "Current"},
    "th_percentile_1y": {"zh": "近1年分位", "en": "1Y %ile"},
    "th_percentile_3y": {"zh": "近3年分位", "en": "3Y %ile"},
    "th_percentile_5y": {"zh": "近5年分位", "en": "5Y %ile"},
    "th_indicator": {"zh": "指标", "en": "Indicator"},
    "th_value": {"zh": "数值", "en": "Value"},
    "th_status": {"zh": "状态", "en": "Status"},
    "th_segment": {"zh": "业务板块", "en": "Segment"},
    "th_share": {"zh": "收入占比", "en": "Share"},
    "th_yoy_growth": {"zh": "同比增速", "en": "YoY Growth"},
    "th_key_driver": {"zh": "核心驱动", "en": "Key Driver"},
    # Misc labels
    "key_takeaway": {"zh": "核心结论", "en": "Key Takeaway"},
    "key_catalysts": {"zh": "核心催化", "en": "Key Catalysts"},
    "probability": {"zh": "触发概率", "en": "Probability"},
    "impact": {"zh": "影响程度", "en": "Impact"},
    "mitigation": {"zh": "缓解因素", "en": "Mitigation"},
    "potential_impact": {"zh": "可能影响", "en": "Potential Impact"},
    "board_structure": {"zh": "董事会结构", "en": "Board Structure"},
    "equity_incentives": {"zh": "股权激励", "en": "Equity Incentives"},
    "dividend_history": {"zh": "历史分红", "en": "Dividend History"},
    "related_party": {"zh": "关联交易", "en": "Related Party Transactions"},
    "shareholding": {"zh": "持股情况", "en": "Shareholding"},
    "segments": {"zh": "客户分群", "en": "Segments"},
    "top5_concentration": {"zh": "前5大客户集中度", "en": "Top 5 Concentration"},
    "cac_ltv": {"zh": "CAC/LTV", "en": "CAC/LTV"},
    "retention": {"zh": "留存率", "en": "Retention"},
    "channel_mix": {"zh": "渠道分布", "en": "Channel Mix"},
    "growth_driver_label": {"zh": "增长驱动", "en": "Growth Driver"},
    "health_assessment": {"zh": "健康度评价", "en": "Health Assessment"},
    "coverage_assessment": {"zh": "覆盖能力评估", "en": "Coverage Assessment"},
    "overall_assessment_label": {"zh": "综合评价", "en": "Overall Assessment"},
    "arrangement": {"zh": "均线排列", "en": "Arrangement"},
    "current_status": {"zh": "当前状态", "en": "Current"},
    "opportunity": {"zh": "增量空间", "en": "Opportunity"},
    "timeline": {"zh": "兑现时间", "en": "Timeline"},
    "drivers": {"zh": "驱动因素", "en": "Drivers"},
    "description": {"zh": "描述", "en": "Description"},
    "nav_label": {"zh": "报告目录", "en": "Contents"},
    "disclaimer": {"zh": "本报告由 SanSi AI 自动生成，仅供参考，不构成投资建议。投资者应根据自身风险承受能力独立做出投资决策。过往表现不代表未来收益。",
                   "en": "This report is generated by SanSi AI for informational purposes only and does not constitute investment advice. Past performance is not indicative of future results."},
    "powered_by": {"zh": "由 SanSi AI 驱动", "en": "Powered by SanSi AI"},
    "not_available": {"zh": "暂无数据", "en": "N/A"},
    # Badges
    "high": {"zh": "高", "en": "High"},
    "medium": {"zh": "中", "en": "Medium"},
    "low": {"zh": "低", "en": "Low"},
    "significant": {"zh": "重大", "en": "Significant"},
    "moderate": {"zh": "中等", "en": "Moderate"},
    "limited": {"zh": "有限", "en": "Limited"},
    "positive": {"zh": "正面", "en": "Positive"},
    "negative": {"zh": "负面", "en": "Negative"},
    "neutral": {"zh": "中性", "en": "Neutral"},
    "buy": {"zh": "买入", "en": "Buy"},
    "sell": {"zh": "减持", "en": "Sell"},
    "hold": {"zh": "持有", "en": "Hold"},
    "outperform": {"zh": "增持", "en": "Outperform"},
    "underperform": {"zh": "减持", "en": "Underperform"},
    "ma5": {"zh": "MA5", "en": "MA5"},
    "ma20": {"zh": "MA20", "en": "MA20"},
    "ma60": {"zh": "MA60", "en": "MA60"},
    "ma120": {"zh": "MA120", "en": "MA120"},
    "ma250": {"zh": "MA250", "en": "MA250"},
    "strong_support": {"zh": "强支撑", "en": "Strong Support"},
    "weak_support": {"zh": "弱支撑", "en": "Weak Support"},
    "weak_resistance": {"zh": "弱压力", "en": "Weak Resistance"},
    "strong_resistance": {"zh": "强压力", "en": "Strong Resistance"},
}

# Porter's Five Forces labels
_PORTER_FORCES_EN = [
    ("Threat of New Entrants", "threat_new_entrants"),
    ("Supplier Power", "supplier_power"),
    ("Buyer Power", "buyer_power"),
    ("Threat of Substitutes", "threat_substitutes"),
    ("Industry Rivalry", "rivalry"),
]
_PORTER_FORCES_ZH = [
    ("新进入者威胁", "threat_new_entrants"),
    ("供应商议价能力", "supplier_power"),
    ("买方议价能力", "buyer_power"),
    ("替代品威胁", "threat_substitutes"),
    ("现有竞争者之间的竞争", "rivalry"),
]

# Financial metrics labels
_METRIC_LABELS = {
    "Revenue": {"zh": "营业收入", "en": "Revenue"},
    "Revenue Growth": {"zh": "营收增速", "en": "Revenue Growth"},
    "Net Income": {"zh": "归母净利润", "en": "Net Income"},
    "Net Income Growth": {"zh": "净利润增速", "en": "Net Income Growth"},
    "Gross Margin": {"zh": "毛利率", "en": "Gross Margin"},
    "EBITDA Margin": {"zh": "EBITDA 率", "en": "EBITDA Margin"},
    "ROE": {"zh": "ROE", "en": "ROE"},
    "EPS": {"zh": "EPS", "en": "EPS"},
    "PE (x)": {"zh": "PE（倍）", "en": "PE (x)"},
    "PB (x)": {"zh": "PB（倍）", "en": "PB (x)"},
    "EV/EBITDA (x)": {"zh": "EV/EBITDA（倍）", "en": "EV/EBITDA (x)"},
    "Dividend Yield": {"zh": "股息率", "en": "Dividend Yield"},
    "Gross Margin": {"zh": "毛利率", "en": "Gross Margin"},
    "EBITDA Margin": {"zh": "EBITDA 率", "en": "EBITDA Margin"},
    "Net Margin": {"zh": "净利率", "en": "Net Margin"},
    "ROE": {"zh": "ROE", "en": "ROE"},
    "ROA": {"zh": "ROA", "en": "ROA"},
    "EPS": {"zh": "EPS", "en": "EPS"},
}

# Segment table headers
_SEGMENT_HEADERS = {
    "zh": ["业务板块", "收入", "收入占比", "同比增速", "毛利率", "核心驱动因素"],
    "en": ["Segment", "Revenue", "Share", "YoY Growth", "Gross Margin", "Key Driver"],
}

# Competitor table headers
_COMPETITOR_HEADERS = {
    "zh": ["公司", "营收", "营收增速", "毛利率", "ROE", "PE", "PB", "市值"],
    "en": ["Company", "Revenue", "Rev Growth", "Gross Margin", "ROE", "PE", "PB", "Market Cap"],
}

# Peer valuation headers
_PEER_VAL_HEADERS = {
    "zh": ["公司", "市值", "PE(TTM)", "PE(2025E)", "PE(2026E)", "PB", "EV/EBITDA", "ROE", "营收增速", "股息率"],
    "en": ["Company", "Market Cap", "PE(TTM)", "PE(2025E)", "PE(2026E)", "PB", "EV/EBITDA", "ROE", "Rev Growth", "Div Yield"],
}


def T(key: str, lang: str = "zh") -> str:
    return _LABELS.get(key, {}).get(lang, key)

def _mt(label: str, lang: str) -> str:
    return _METRIC_LABELS.get(label, {}).get(lang, label)


# ================================================================
# Markdown → HTML helpers
# ================================================================

def _md_to_html(text: str) -> str:
    if not text:
        return ""
    lines = text.split('\n')
    out = []
    in_list = False
    for line in lines:
        s = line.strip()
        if not s:
            if in_list:
                out.append('</ul>')
                in_list = False
            out.append('')
            continue
        if s.startswith('### '):
            if in_list: out.append('</ul>'); in_list = False
            c = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[4:])
            out.append(f'<h4 class="h4">{c}</h4>')
            continue
        if s.startswith('## '):
            if in_list: out.append('</ul>'); in_list = False
            c = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[3:])
            out.append(f'<h3 class="h3">{c}</h3>')
            continue
        if s.startswith('- '):
            if not in_list: out.append('<ul class="ulist">'); in_list = True
            item = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[2:])
            out.append(f'<li>{item}</li>')
            continue
        if in_list: out.append('</ul>'); in_list = False
        c = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        out.append(f'<p class="body">{c}</p>')
    if in_list: out.append('</ul>')
    return '\n'.join(out)


def _safe_get(d: dict, key: str, default: Any = None, lang: str = "zh") -> Any:
    if not isinstance(d, dict): return default
    return d.get(key, default)


def _na(lang: str = "zh") -> str:
    return T("not_available", lang)


def _grid_card(label: str, value: str) -> str:
    return f'''<div class="metric-card"><span class="metric-label">{label}</span><span class="metric-value">{value}</span></div>'''


def _rating_badge(rating: str, lang: str = "zh") -> str:
    r = str(rating).strip().lower()
    buy_words = ('buy', 'outperform', 'overweight', 'strong buy', '买入', '增持')
    sell_words = ('sell', 'underperform', 'underweight', 'strong sell', '减持')
    if r in buy_words: cls = 'badge-buy'; label = T("buy", lang)
    elif r in sell_words: cls = 'badge-sell'; label = T("sell", lang)
    else: cls = 'badge-hold'; label = T("hold", lang)
    return f'<span class="rating-badge {cls}">{label}</span>'


def _prob_badge(prob: str, lang: str = "zh") -> str:
    p = str(prob).lower()
    if '高' in p or p == 'high': return f'<span class="badge-high">{T("high", lang)}</span>'
    elif '中' in p or p == 'medium': return f'<span class="badge-med">{T("medium", lang)}</span>'
    return f'<span class="badge-low">{T("low", lang)}</span>'


def _impact_badge(impact: str, lang: str = "zh") -> str:
    p = str(impact).lower()
    if '重大' in p or p == 'significant': return f'<span class="badge-high">{T("significant", lang)}</span>'
    elif '中等' in p or p == 'moderate': return f'<span class="badge-med">{T("moderate", lang)}</span>'
    return f'<span class="badge-low">{T("limited", lang)}</span>'


# ================================================================
# Module renderers
# ================================================================

def _render_module_1_investment_thesis(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'

    html = ''
    rb = data.get('rating_box', {})
    theses = data.get('core_theses', [])
    snap = data.get('financial_snapshot', {})
    summary = data.get('executive_summary', '')

    # Rating box
    html += '<table class="data-table mb-6"><thead><tr>'
    html += f'<th>{T("th_item", lang)}</th><th>{T("th_content", lang)}</th></tr></thead><tbody>'
    for key, lbl in [('rating', T("rating", lang)), ('current_price', T("current_price", lang)),
                      ('target_price', T("target_price", lang)), ('week_52_range', T("week_52_range", lang)),
                      ('total_market_cap', T("market_cap", lang)), ('float_market_cap', T("float_market_cap", lang))]:
        html += f'<tr><td class="font-semibold">{lbl}</td><td>{_safe_get(rb, key, _na(lang))}</td></tr>'
    html += '</tbody></table>'

    if theses:
        html += f'<h3 class="h3">{T("core_theses", lang)}</h3>'
        for i, t in enumerate(theses, 1):
            title = t.get('thesis_title', '')
            exp = t.get('expansion', '')
            html += f'<div class="highlight-box"><p class="thesis-title">{T("thesis_prefix", lang)} {i}: {title}</p><p class="body">{exp}</p></div>'

    years = snap.get('years', [])
    if years:
        html += f'<h3 class="h3">{T("financial_snapshot", lang)}</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Metric</th>'
        for y in years: html += f'<th>{y}</th>'
        html += '</tr></thead><tbody>'
        for label, key in [('Revenue','revenue'),('Revenue Growth','revenue_growth'),('Net Income','net_income'),
                           ('Net Income Growth','net_income_growth'),('Gross Margin','gross_margin'),
                           ('EBITDA Margin','ebitda_margin'),('ROE','roe'),('EPS','eps'),
                           ('PE (x)','pe'),('PB (x)','pb'),('EV/EBITDA (x)','ev_ebitda'),('Dividend Yield','dividend_yield')]:
            html += f'<tr><td class="font-semibold">{_mt(label, lang)}</td>'
            for v in snap.get(key, []): html += f'<td>{v}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'

    if summary:
        html += f'<div class="highlight-box mt-6"><p class="body font-medium">{summary}</p></div>'
    return html


def _render_module_2_investment_rationale(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    pillars = data.get('pillars', [])
    if pillars:
        html += f'<h3 class="section-subtitle">{T("investment_pillars", lang)}</h3>'
        for i, p in enumerate(pillars, 1):
            html += f'<div class="content-card mb-4"><h4 class="h4" style="color:#6366f1;">{T("pillar_prefix", lang)} {i}: {p.get("pillar_title","")}</h4>'
            for field, lbl in [('market_opportunity', T("market_opportunity", lang)),
                               ('competitive_advantage', T("competitive_advantage", lang)),
                               ('financial_impact', T("financial_impact", lang))]:
                html += f'<div class="pillar-block"><strong>{lbl}:</strong> {_md_to_html(p.get(field,""))}</div>'
            html += '</div>'

    for risks, title in [(data.get('company_risks',[]), T("company_risks", lang)),
                         (data.get('industry_risks',[]), T("industry_risks", lang))]:
        if risks:
            html += f'<h3 class="section-subtitle">{title}</h3>'
            for r in risks:
                html += f'<div class="risk-item"><p><strong>{r.get("risk_title","")}</strong> {_prob_badge(r.get("probability",""), lang)} {_impact_badge(r.get("impact",""), lang)}</p><p class="body">{r.get("description","")}</p><p class="body text-sm muted">{T("mitigation", lang)}: {r.get("mitigation", _na(lang))}</p></div>'

    kt = data.get('key_takeaway','')
    if kt: html += f'<div class="highlight-box mt-4"><p class="body font-medium">{kt}</p></div>'
    return html


def _render_module_3_industry_analysis(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    mo = data.get('market_overview', {})
    if mo:
        html += f'<h3 class="section-subtitle">{T("industry_overview", lang)}</h3>'
        html += '<div class="content-card">'
        for key, lbl in [('industry_name', T("industry_name", lang)), ('industry_boundary', T("industry_boundary", lang)),
                          ('market_size_global', T("market_size_global", lang)), ('market_size_china', 'China/APAC Size'),
                          ('historical_cagr_3_5yr', T("historical_cagr", lang)), ('forecast_cagr_3_5yr', T("forecast_cagr", lang)),
                          ('lifecycle_stage', T("lifecycle_stage", lang))]:
            v = _safe_get(mo, key, _na(lang))
            html += f'<p class="body"><strong>{lbl}:</strong> {v}</p>'
        html += f'<p class="body text-sm muted">{_safe_get(mo, "lifecycle_rationale","")}</p></div>'

    ic = data.get('industry_chain', {})
    if ic:
        html += f'<h3 class="section-subtitle">{T("industry_chain", lang)}</h3>'
        html += '<div class="content-card">'
        for key, lbl in [('chain_description', T("chain_description", lang)), ('value_distribution', T("value_distribution", lang)),
                          ('company_position', T("company_position_chain", lang))]:
            html += f'<p class="body"><strong>{lbl}:</strong> {_safe_get(ic, key, _na(lang))}</p>'
        html += '</div>'

    cl = data.get('competitive_landscape', {})
    if cl:
        html += f'<h3 class="section-subtitle">{T("competitive_landscape", lang)}</h3>'
        html += f'<p class="body"><strong>{T("concentration", lang)}:</strong> {_safe_get(cl, "concentration", _na(lang))} | <strong>{T("competition_intensity", lang)}:</strong> {_safe_get(cl, "competition_intensity", _na(lang))}</p>'
        html += f'<p class="body"><strong>{T("company_rank", lang)}:</strong> {_safe_get(cl, "company_rank", _na(lang))}</p>'
        competitors = cl.get('competitors', [])
        if competitors:
            hdrs = _COMPETITOR_HEADERS[lang]
            html += f'<div class="table-wrap"><table class="data-table"><thead><tr>{"".join(f"<th>{h}</th>" for h in hdrs)}</tr></thead><tbody>'
            for c in competitors:
                html += f'<tr><td class="font-semibold">{c.get("company_name","")}</td><td>{c.get("revenue","")}</td><td>{c.get("revenue_growth","")}</td><td>{c.get("gross_margin","")}</td><td>{c.get("roe","")}</td><td>{c.get("pe","")}</td><td>{c.get("pb","")}</td><td>{c.get("market_cap","")}</td></tr>'
            html += '</tbody></table></div>'

    pf = data.get('porter_five_forces', {})
    if pf:
        html += f'<h3 class="section-subtitle">{T("porter_five", lang)}</h3>'
        forces = _PORTER_FORCES_ZH if lang == "zh" else _PORTER_FORCES_EN
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_force", lang)}</th><th>{T("th_intensity", lang)}</th><th>{T("th_analysis", lang)}</th></tr></thead><tbody>'
        for label, key in forces:
            val = _safe_get(pf, key, _na(lang))
            html += f'<tr><td class="font-semibold">{label}</td><td>{val}</td><td>{val}</td></tr>'
        html += '</tbody></table></div>'

    trends = data.get('trends', [])
    if trends:
        html += f'<h3 class="section-subtitle">{T("key_trends", lang)}</h3>'
        for t in trends:
            html += f'<div class="content-card mb-3"><h4 class="h4">{t.get("trend_name","")}</h4>'
            html += f'<p class="body">{t.get("description","")}</p>'
            html += f'<p class="body text-sm"><strong>{T("drivers", lang)}:</strong> {t.get("drivers","")}</p>'
            html += f'<p class="body text-sm"><strong>{T("impact_on_company", lang)}:</strong> {t.get("impact_on_company","")}</p>'
            html += f'<p class="body text-sm"><strong>{T("timeline", lang)}:</strong> {t.get("timeline","")}</p></div>'

    kt = data.get('key_takeaway','')
    if kt: html += f'<div class="highlight-box mt-4"><p class="body font-medium"><strong>{T("key_takeaway", lang)}:</strong> {kt}</p></div>'
    return html


def _render_module_4_company_analysis(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    co = data.get('company_overview', {})
    if co:
        html += f'<h3 class="section-subtitle">{T("company_overview", lang)}</h3>'
        for key, lbl in [('one_liner', T("one_liner", lang)), ('business_model', T("business_model", lang)),
                          ('customers', T("customers", lang)), ('scale', T("scale", lang)),
                          ('ownership', T("ownership", lang))]:
            html += f'<p class="body"><strong>{lbl}:</strong> {_safe_get(co, key, _na(lang))}</p>'

    milestones = data.get('milestones', [])
    if milestones:
        html += f'<h3 class="section-subtitle">{T("milestones", lang)}</h3>'
        html += '<div class="timeline">'
        for m in milestones:
            html += f'<div class="timeline-item"><span class="timeline-year">{m.get("year","")}</span><span>{m.get("event","")}</span></div>'
        html += '</div>'

    execs = data.get('executives', [])
    if execs:
        html += f'<h3 class="section-subtitle">{T("management_team", lang)}</h3>'
        for e in execs:
            html += f'<div class="content-card mb-3"><h4 class="h4">{e.get("name","")} — {e.get("title","")} (since {e.get("tenure","")})</h4>'
            html += f'<p class="body">{e.get("background","")}</p><p class="body text-sm muted">{T("shareholding", lang)}: {e.get("shareholding", _na(lang))}</p></div>'

    gov = data.get('governance', {})
    if gov:
        html += f'<h3 class="section-subtitle">{T("governance", lang)}</h3>'
        for key, lbl in [('board_structure', T("board_structure", lang)), ('equity_incentives', T("equity_incentives", lang)),
                          ('dividend_history', T("dividend_history", lang)), ('related_party', T("related_party", lang))]:
            v = gov.get(key, '')
            if v: html += f'<p class="body"><strong>{lbl}:</strong> {v}</p>'

    segments = data.get('business_segments', [])
    if segments:
        html += f'<h3 class="section-subtitle">{T("business_segments", lang)}</h3>'
        hdrs = _SEGMENT_HEADERS[lang]
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr>{"".join(f"<th>{h}</th>" for h in hdrs)}</tr></thead><tbody>'
        for s in segments:
            html += f'<tr><td class="font-semibold">{s.get("name","")}</td><td>{s.get("revenue","")}</td><td>{s.get("revenue_share","")}</td><td>{s.get("yoy_growth","")}</td><td>{s.get("gross_margin","")}</td><td>{s.get("key_driver","")}</td></tr>'
        html += '</tbody></table></div>'

    moat = data.get('moat_analysis', {})
    if moat:
        html += f'<h3 class="section-subtitle">{T("moat_analysis", lang)}</h3>'
        html += f'<p class="body"><strong>{T("moat_overall", lang)}:</strong> {_safe_get(moat, "overall_moat_rating", _na(lang))}</p>'
        for dim in ['brand_barrier','tech_barrier','channel_barrier','scale_barrier','switching_cost']:
            v = moat.get(dim, '')
            if v: html += f'<p class="body"><strong>{dim.replace("_"," ").title()}:</strong> {v}</p>'

    short = data.get('short_term_drivers', [])
    medium = data.get('medium_term_drivers', [])
    if short or medium:
        html += f'<h3 class="section-subtitle">{T("growth_drivers", lang)}</h3>'
        for title, drivers in [(T("short_term_drivers", lang), short), (T("medium_term_drivers", lang), medium)]:
            if drivers:
                html += f'<h4 class="h4">{title}</h4>'
                for d in drivers:
                    html += f'<div class="content-card mb-2"><p class="body"><strong>{d.get("driver_name","")}</strong></p><p class="body text-sm">{T("current_status", lang)}: {d.get("current_status","")} → {T("opportunity", lang)}: {d.get("incremental_opportunity","")}</p><p class="body text-sm muted">{T("timeline", lang)}: {d.get("timeline","")}</p></div>'

    ca = data.get('customer_analysis', {})
    if ca:
        html += f'<h3 class="section-subtitle">{T("customer_analysis", lang)}</h3>'
        for key, lbl in [('customer_segments', T("segments", lang)), ('top5_concentration', T("top5_concentration", lang)),
                          ('cac_ltv', T("cac_ltv", lang)), ('retention', T("retention", lang)),
                          ('channel_mix', T("channel_mix", lang))]:
            v = ca.get(key, '')
            if v: html += f'<p class="body"><strong>{lbl}:</strong> {v}</p>'

    return html


def _render_module_5_financial_analysis(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    ra = data.get('revenue_analysis', {})
    if ra:
        html += f'<h3 class="section-subtitle">{T("revenue_analysis", lang)}</h3>'
        html += f'<p class="body">{_safe_get(ra, "revenue_trend", _na(lang))}</p>'
        html += f'<p class="body">{_safe_get(ra, "revenue_mix_change", _na(lang))}</p>'
        html += f'<p class="body"><strong>{T("growth_driver_label", lang)}:</strong> {_safe_get(ra, "volume_vs_price", _na(lang))}</p>'

    pa = data.get('profitability_analysis', {})
    if pa:
        html += f'<h3 class="section-subtitle">{T("profitability_analysis", lang)}</h3>'
        tbl = pa.get('table', {})
        years = tbl.get('years', [])
        if years:
            html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_metric", lang)}</th>{"".join(f"<th>{y}</th>" for y in years)}</tr></thead><tbody>'
            for label, key in [('Gross Margin','gross_margin'),('EBITDA Margin','ebitda_margin'),('Net Margin','net_margin'),('ROE','roe'),('ROA','roa'),('EPS','eps')]:
                html += f'<tr><td class="font-semibold">{_mt(label, lang)}</td>{"".join(f"<td>{v}</td>" for v in tbl.get(key,[]))}</tr>'
            html += '</tbody></table></div>'
        html += f'<p class="body">{_safe_get(pa, "margin_attribution", "")}</p><p class="body">{_safe_get(pa, "roe_drivers", "")}</p>'

    dup = data.get('dupont_analysis', {})
    if dup:
        html += f'<h3 class="section-subtitle">{T("dupont_analysis", lang)}</h3>'
        dyears = dup.get('years', [])
        if dyears:
            html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_item", lang)}</th>{"".join(f"<th>{y}</th>" for y in dyears)}</tr></thead><tbody>'
            for label, key in [('ROE','roe_values'),('= Net Margin','net_margin_values'),('x Asset Turnover','asset_turnover_values'),('x Equity Multiplier','equity_multiplier_values')]:
                html += f'<tr><td class="font-semibold">{label}</td>{"".join(f"<td>{v}</td>" for v in dup.get(key,[]))}</tr>'
            html += '</tbody></table></div>'
        html += f'<p class="body"><strong>{T("key_takeaway", lang)}:</strong> {_safe_get(dup, "driver_conclusion", _na(lang))}</p>'

    oe = data.get('operating_efficiency', {})
    if oe:
        html += f'<h3 class="section-subtitle">{T("operating_efficiency", lang)}</h3>'
        html += f'<p class="body">{_safe_get(oe, "analysis", _na(lang))}</p>'

    cf = data.get('cash_flow_analysis', {})
    if cf:
        html += f'<h3 class="section-subtitle">{T("cash_flow_analysis", lang)}</h3>'
        html += f'<p class="body"><strong>{T("health_assessment", lang)}:</strong> {_safe_get(cf, "health_assessment", _na(lang))}</p>'
        html += f'<p class="body"><strong>{T("coverage_assessment", lang)}:</strong> {_safe_get(cf, "coverage_assessment", _na(lang))}</p>'

    cm = data.get('credit_metrics', {})
    if cm:
        html += f'<h3 class="section-subtitle">{T("credit_metrics", lang)}</h3>'
        html += f'<p class="body"><strong>{T("overall_assessment_label", lang)}:</strong> {_safe_get(cm, "overall_assessment", _na(lang))}</p>'

    ik = data.get('industry_kpis', {})
    kpis = ik.get('kpis', [])
    if kpis:
        html += f'<h3 class="section-subtitle">{T("industry_kpis", lang)} ({_safe_get(ik, "industry_type", "")})</h3>'
        for k in kpis:
            html += f'<p class="body"><strong>{k.get("name","")}:</strong> {k.get("value","")} — {k.get("interpretation","")}</p>'

    kt = data.get('key_takeaway','')
    if kt: html += f'<div class="highlight-box mt-4"><p class="body font-medium"><strong>{T("key_takeaway", lang)}:</strong> {kt}</p></div>'
    return html


def _render_module_6_earnings_forecast(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    assumptions = data.get('assumptions', [])
    if assumptions:
        html += f'<h3 class="section-subtitle">{T("core_assumptions", lang)}</h3>'
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_parameter", lang)}</th><th>{T("th_value_2025e", lang)}</th><th>{T("th_value_2026e", lang)}</th><th>{T("th_value_2027e", lang)}</th><th>{T("th_rationale", lang)}</th></tr></thead><tbody>'
        for a in assumptions:
            html += f'<tr><td class="font-semibold">{a.get("parameter","")}</td><td>{a.get("value_2025e","")}</td><td>{a.get("value_2026e","")}</td><td>{a.get("value_2027e","")}</td><td class="text-sm">{a.get("rationale","")}</td></tr>'
        html += '</tbody></table></div>'

    ist = data.get('income_statement', {})
    items = ist.get('line_items', [])
    if items:
        html += f'<h3 class="section-subtitle">{T("forecast_income_statement", lang)}</h3>'
        v25, v26, v27 = ist.get('values_2025e',[]), ist.get('values_2026e',[]), ist.get('values_2027e',[])
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_line_item", lang)}</th><th>{T("th_value_2025e", lang)}</th><th>{T("th_value_2026e", lang)}</th><th>{T("th_value_2027e", lang)}</th></tr></thead><tbody>'
        for i, item in enumerate(items):
            html += f'<tr><td class="font-semibold">{item}</td><td>{v25[i] if i<len(v25) else _na(lang)}</td><td>{v26[i] if i<len(v26) else _na(lang)}</td><td>{v27[i] if i<len(v27) else _na(lang)}</td></tr>'
        html += '</tbody></table></div>'

    scenarios = data.get('scenarios', [])
    if scenarios:
        html += f'<h3 class="section-subtitle">{T("scenario_analysis", lang)}</h3>'
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_scenario", lang)}</th><th>{T("th_assumptions", lang)}</th><th>{T("th_revenue", lang)} 2025E</th><th>EPS 2025E</th><th>{T("th_target_price", lang)}</th><th>{T("th_probability", lang)}</th></tr></thead><tbody>'
        for s in scenarios:
            html += f'<tr><td class="font-semibold">{s.get("name","")}</td><td class="text-sm">{s.get("assumptions","")}</td><td>{s.get("revenue_2025e","")}</td><td>{s.get("eps_2025e","")}</td><td>{s.get("target_price","")}</td><td>{s.get("probability","")}</td></tr>'
        html += '</tbody></table></div>'

    kt = data.get('key_takeaway','')
    if kt: html += f'<div class="highlight-box mt-4"><p class="body font-medium">{kt}</p></div>'
    return html


def _render_module_7_valuation_analysis(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    dcf = data.get('dcf_analysis', {})
    if dcf:
        html += f'<h3 class="section-subtitle">{T("dcf_valuation", lang)}</h3>'
        html += f'<p class="body"><strong>{T("target_price", lang)}:</strong> {_safe_get(dcf,"target_price",_na(lang))} ({T("th_price_range", lang)}: {_safe_get(dcf,"low_estimate",_na(lang))} – {_safe_get(dcf,"high_estimate",_na(lang))})</p>'
        assumptions = dcf.get('assumptions', [])
        if assumptions:
            html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_parameter", lang)}</th><th>{T("th_value", lang)}</th><th>{T("th_rationale", lang)}</th></tr></thead><tbody>'
            for a in assumptions:
                html += f'<tr><td class="font-semibold">{a.get("parameter","")}</td><td>{a.get("value","")}</td><td class="text-sm">{a.get("rationale","")}</td></tr>'
            html += '</tbody></table></div>'

    pc = data.get('peer_comparison', {})
    if pc:
        html += f'<h3 class="section-subtitle">{T("peer_comparison", lang)}</h3>'
        html += f'<p class="body text-sm muted"><strong>{T("selection_criteria", lang)}:</strong> {_safe_get(pc,"selection_rationale","")}</p>'
        peers = pc.get('peers', [])
        if peers:
            hdrs = _PEER_VAL_HEADERS[lang]
            html += f'<div class="table-wrap"><table class="data-table"><thead><tr>{"".join(f"<th>{h}</th>" for h in hdrs)}</tr></thead><tbody>'
            tc = pc.get('target_company', {})
            if tc.get('company_name'):
                html += f'<tr class="font-semibold bg-indigo-50"><td>{tc.get("company_name","")}</td><td>{tc.get("market_cap","")}</td><td>{tc.get("pe_ttm","")}</td><td>{tc.get("pe_2025e","")}</td><td>{tc.get("pe_2026e","")}</td><td>{tc.get("pb","")}</td><td>{tc.get("ev_ebitda","")}</td><td>{tc.get("roe","")}</td><td>{tc.get("revenue_growth","")}</td><td>{tc.get("dividend_yield","")}</td></tr>'
            for p in peers:
                html += f'<tr><td>{p.get("company_name","")}</td><td>{p.get("market_cap","")}</td><td>{p.get("pe_ttm","")}</td><td>{p.get("pe_2025e","")}</td><td>{p.get("pe_2026e","")}</td><td>{p.get("pb","")}</td><td>{p.get("ev_ebitda","")}</td><td>{p.get("roe","")}</td><td>{p.get("revenue_growth","")}</td><td>{p.get("dividend_yield","")}</td></tr>'
            for row_key, label in [('max_values','Max'),('percentile_75','75%'),('median','Median'),('percentile_25','25%'),('min_values','Min')]:
                row = pc.get(row_key, {})
                if row.get('company_name'):
                    html += f'<tr class="font-semibold bg-slate-50"><td>{label}</td><td>{row.get("market_cap","")}</td><td>{row.get("pe_ttm","")}</td><td>{row.get("pe_2025e","")}</td><td>{row.get("pe_2026e","")}</td><td>{row.get("pb","")}</td><td>{row.get("ev_ebitda","")}</td><td>{row.get("roe","")}</td><td>{row.get("revenue_growth","")}</td><td>{row.get("dividend_yield","")}</td></tr>'
            html += '</tbody></table></div>'

    hr = data.get('historical_range', [])
    if hr:
        html += f'<h3 class="section-subtitle">{T("historical_valuation", lang)}</h3>'
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_metric", lang)}</th><th>{T("th_current", lang)}</th><th>{T("th_percentile_1y", lang)}</th><th>{T("th_percentile_3y", lang)}</th><th>{T("th_percentile_5y", lang)}</th></tr></thead><tbody>'
        for h in hr:
            html += f'<tr><td class="font-semibold">{h.get("metric","")}</td><td>{h.get("current_value","")}</td><td>{h.get("percentile_1y","")}</td><td>{h.get("percentile_3y","")}</td><td>{h.get("percentile_5y","")}</td></tr>'
        html += '</tbody></table></div>'

    vs = data.get('valuation_summary', [])
    if vs:
        html += f'<h3 class="section-subtitle">{T("valuation_summary", lang)}</h3>'
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_method", lang)}</th><th>{T("th_weight", lang)}</th><th>{T("th_price_range", lang)}</th><th>{T("th_weighted_price", lang)}</th></tr></thead><tbody>'
        for v in vs:
            html += f'<tr><td class="font-semibold">{v.get("method","")}</td><td>{v.get("weight","")}</td><td>{v.get("price_range","")}</td><td>{v.get("weighted_price","")}</td></tr>'
        html += '</tbody></table></div>'

    rating = data.get('rating', {})
    if rating:
        html += f'<h3 class="section-subtitle">{T("rating_recommendation", lang)}</h3>'
        html += f'<div class="content-card" style="display:flex;flex-wrap:wrap;gap:1.5rem;align-items:center;">'
        html += f'<div><span class="metric-label">{T("current_price", lang)}</span><p class="metric-value">{_safe_get(rating,"current_price",_na(lang))}</p></div>'
        html += f'<div><span class="metric-label">{T("target_12m", lang)}</span><p class="metric-value" style="color:#6366f1;">{_safe_get(rating,"target_price_12m",_na(lang))}</p></div>'
        html += f'<div><span class="metric-label">Upside/Downside</span><p class="metric-value">{_safe_get(rating,"upside_pct","")} / {_safe_get(rating,"downside_pct","")}</p></div>'
        html += f'<div>{_rating_badge(_safe_get(rating,"rating",""), lang)}</div></div>'
        html += f'<p class="body mt-3"><strong>{T("key_catalysts", lang)}:</strong> {_safe_get(rating,"catalysts",_na(lang))}</p>'
        html += f'<p class="body"><strong>{T("suitable_style", lang)}:</strong> {_safe_get(rating,"suitable_style",_na(lang))} | <strong>{T("unsuitable_style", lang)}:</strong> {_safe_get(rating,"unsuitable_style",_na(lang))}</p>'

    kt = data.get('key_takeaway','')
    if kt: html += f'<div class="highlight-box mt-4"><p class="body font-medium">{kt}</p></div>'
    return html


def _render_module_8_technical_analysis(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    ta = data.get('trend_assessment', {})
    if ta:
        html += f'<h3 class="section-subtitle">{T("trend_assessment", lang)}</h3>'
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_indicator", lang)}</th><th>{T("th_value", lang)}</th><th>{T("th_status", lang)}</th></tr></thead><tbody>'
        for key in ['ma5','ma20','ma60','ma120','ma250']:
            html += f'<tr><td class="font-semibold">{T(key, lang)}</td><td>{ta.get(key, _na(lang))}</td><td>{ta.get(key+"_status", _na(lang))}</td></tr>'
        html += f'<tr><td class="font-semibold">{T("arrangement", lang)}</td><td colspan="2">{ta.get("arrangement", _na(lang))}</td></tr>'
        html += '</tbody></table></div>'

    kl = data.get('key_levels', [])
    if kl:
        html += f'<h3 class="section-subtitle">{T("key_levels", lang)}</h3>'
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_type", lang)}</th><th>{T("th_price", lang)}</th><th>{T("th_basis", lang)}</th></tr></thead><tbody>'
        for l in kl:
            html += f'<tr><td class="font-semibold">{l.get("level_type","")}</td><td>{l.get("price","")}</td><td class="text-sm">{l.get("basis","")}</td></tr>'
        html += '</tbody></table></div>'

    mom = data.get('momentum', {})
    if mom:
        html += f'<h3 class="section-subtitle">{T("momentum_volume", lang)}</h3>'
        html += '<div class="content-card">'
        html += f'<p class="body"><strong>RSI(14):</strong> {_safe_get(mom,"rsi14",_na(lang))} — {_safe_get(mom,"rsi_interpretation",_na(lang))}</p>'
        html += f'<p class="body"><strong>MACD:</strong> {_safe_get(mom,"macd_status",_na(lang))}</p>'
        html += f'<p class="body"><strong>20D:</strong> {_safe_get(mom,"change_20d",_na(lang))} | <strong>60D:</strong> {_safe_get(mom,"change_60d",_na(lang))}</p>'
        html += f'<p class="body"><strong>Volume:</strong> {_safe_get(mom,"volume_signal",_na(lang))}</p>'
        html += '</div>'

    for label, key in [(T("bullish_trigger", lang), 'bullish_trigger'), (T("bearish_trigger", lang), 'bearish_trigger')]:
        v = data.get(key, '')
        if v:
            color = '#10b981' if 'bullish' in key else '#ef4444'
            html += f'<div class="content-card mb-2" style="border-left:4px solid {color};"><p class="body"><strong>{label}:</strong> {v}</p></div>'

    ts = data.get('trend_summary','')
    if ts: html += f'<div class="highlight-box mt-4"><p class="body font-medium"><strong>{T("tech_summary", lang)}:</strong> {ts}</p></div>'
    return html


def _render_module_9_monitor_signals(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    signals = data.get('signals', [])
    if signals:
        html += f'<h3 class="section-subtitle">{T("monitor_signals", lang)}</h3>'
        html += f'<div class="table-wrap"><table class="data-table"><thead><tr><th>{T("th_rank", lang)}</th><th>{T("th_signal", lang)}</th><th>{T("th_observation", lang)}</th><th>{T("th_positive_signal", lang)}</th><th>{T("th_negative_signal", lang)}</th></tr></thead><tbody>'
        for s in signals:
            html += f'<tr><td>{s.get("rank","")}</td><td class="font-semibold">{s.get("signal_name","")}</td><td class="text-sm">{s.get("observation_method","")}</td><td class="text-sm" style="color:#059669;">{s.get("positive_signal","")}</td><td class="text-sm" style="color:#dc2626;">{s.get("negative_signal","")}</td></tr>'
        html += '</tbody></table></div>'

    freq = data.get('monitoring_frequency', '')
    if freq: html += f'<p class="body text-sm muted">{T("monitoring_frequency", lang)}: <strong>{freq}</strong></p>'
    return html


def _render_module_10_risk_disclosure(data: dict, lang: str) -> str:
    if not data: return f'<p class="body muted">{T("not_available", lang)}</p>'
    html = ''

    for category, title_key in [('macro_risks','macro_risks'),('industry_risks','industry_risks_title'),
                                  ('operational_risks','operational_risks'),('valuation_risks','valuation_risks')]:
        risks = data.get(category, [])
        if risks:
            html += f'<h3 class="section-subtitle">{T(title_key, lang)}</h3>'
            for r in risks:
                html += f'<div class="risk-item"><p><strong>{r.get("risk_name","")}</strong> {_prob_badge(r.get("probability",""), lang)} {_impact_badge(r.get("impact",""), lang)}</p><p class="body">{r.get("description","")}</p><p class="body text-sm muted">{T("potential_impact", lang)}: {r.get("potential_impact_detail","")}</p><p class="body text-sm muted">{T("mitigation", lang)}: {r.get("mitigation", _na(lang))}</p></div>'

    rs = data.get('risk_summary', '')
    if rs: html += f'<div class="highlight-box mt-4" style="border-left-color:#f59e0b;"><p class="body font-medium"><strong>{T("risk_reward_summary", lang)}:</strong> {rs}</p></div>'
    return html


# ================================================================
# CSS
# ================================================================

CSS_STYLES = """
<style>
    :root { --accent: #6366f1; --text: #0f172a; --muted: #64748b; --border: #e2e8f0; --bg-card: #f8fafc; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif; color: var(--text); background: #fff; line-height: 1.6; }
    .max-w { max-width: 960px; margin: 0 auto; padding: 0 1.5rem; }
    .hero { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 2.5rem 2rem 1.5rem; }
    .hero h1 { color: #fff; font-size: 2rem; font-weight: 700; }
    .hero .ticker { background: #1e293b; border: 1px solid #334155; color: #94a3b8; padding: 0.2rem 0.6rem; border-radius: 0.375rem; font-size: 0.8rem; font-weight: 500; }
    .hero .sector { color: #94a3b8; font-size: 0.85rem; }
    .hero .price-label { color: #64748b; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; }
    .hero .price { color: #fff; font-size: 1.5rem; font-weight: 700; }
    .hero .target { color: #a5b4fc; font-size: 1.5rem; font-weight: 700; }
    .rating-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 700; letter-spacing: 0.02em; }
    .badge-buy { background: #d1fae5; color: #065f46; }
    .badge-sell { background: #fee2e2; color: #991b1b; }
    .badge-hold { background: #fef3c7; color: #92400e; }
    .badge-high { background: #fee2e2; color: #991b1b; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }
    .badge-med { background: #fef3c7; color: #92400e; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }
    .badge-low { background: #d1fae5; color: #065f46; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; margin: 1.5rem 0; }
    .metric-card { background: #fff; border: 1px solid var(--border); border-radius: 0.75rem; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); position: relative; overflow: hidden; }
    .metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--accent); }
    .metric-label { display: block; color: var(--muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }
    .metric-value { display: block; color: var(--text); font-size: 1rem; font-weight: 600; }
    .section { margin: 2.5rem 0; padding-top: 1rem; }
    .section-title { font-size: 1.4rem; font-weight: 700; color: var(--text); border-left: 4px solid var(--accent); padding-left: 0.75rem; margin-bottom: 1.5rem; }
    .section-subtitle { font-size: 1.1rem; font-weight: 600; color: #1e293b; margin: 1.5rem 0 0.75rem; }
    .h3 { font-size: 1rem; font-weight: 600; color: #0f172a; margin: 1rem 0 0.5rem; border-left: 3px solid var(--accent); padding-left: 0.6rem; }
    .h4 { font-size: 0.9rem; font-weight: 600; color: #334155; margin: 0.75rem 0 0.4rem; }
    .body { font-size: 0.875rem; color: #334155; line-height: 1.7; margin-bottom: 0.5rem; }
    .muted { color: var(--muted); }
    .text-sm { font-size: 0.8rem; }
    .font-semibold { font-weight: 600; }
    .font-medium { font-weight: 500; }
    .highlight-box { background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%); border-left: 4px solid var(--accent); border-radius: 0.75rem; padding: 1.25rem 1.5rem; margin: 1rem 0; }
    .thesis-title { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem; }
    .content-card { background: var(--bg-card); border-radius: 0.75rem; padding: 1.25rem; border: 1px solid var(--border); margin-bottom: 0.5rem; }
    .pillar-block { margin: 0.5rem 0; }
    .risk-item { background: #fff; border: 1px solid var(--border); border-radius: 0.5rem; padding: 0.75rem 1rem; margin-bottom: 0.5rem; }
    .risk-item:hover { border-color: #cbd5e1; }
    .timeline { padding: 0.5rem 0; }
    .timeline-item { display: flex; gap: 1rem; padding: 0.4rem 0; font-size: 0.875rem; border-bottom: 1px solid #f1f5f9; }
    .timeline-year { font-weight: 700; color: var(--accent); min-width: 3.5rem; }
    .table-wrap { overflow-x: auto; margin: 0.75rem 0 1.25rem; }
    .data-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.8rem; border-radius: 0.5rem; overflow: hidden; border: 1px solid var(--border); }
    .data-table th { background: #f1f5f9; color: #475569; padding: 0.6rem 0.75rem; text-align: left; font-weight: 600; font-size: 0.75rem; white-space: nowrap; }
    .data-table td { padding: 0.55rem 0.75rem; border-top: 1px solid #f1f5f9; white-space: nowrap; }
    .data-table tr:hover { background: #f8fafc; }
    .bg-slate-50 { background: #f8fafc !important; }
    .bg-indigo-50 { background: #eef2ff !important; }
    .ulist { list-style: none; padding-left: 0; margin: 0.35rem 0; }
    .ulist li { padding: 0.3rem 0 0.3rem 1.2rem; position: relative; font-size: 0.875rem; color: #334155; line-height: 1.6; }
    .ulist li::before { content: '›'; position: absolute; left: 0; color: var(--accent); font-weight: 700; font-size: 1.1rem; }
    .module-nav { background: #f8fafc; border-bottom: 1px solid var(--border); padding: 0.75rem 0; position: sticky; top: 0; z-index: 10; }
    .module-nav a { font-size: 0.75rem; color: var(--muted); text-decoration: none; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
    .module-nav a:hover { color: var(--accent); background: #eef2ff; }
    .disclaimer { background: #f8fafc; padding: 1.5rem; border-radius: 0.75rem; margin-top: 3rem; color: #94a3b8; font-size: 0.65rem; line-height: 1.5; }
    .mb-2 { margin-bottom: 0.5rem; } .mb-3 { margin-bottom: 0.75rem; } .mb-4 { margin-bottom: 1rem; } .mb-6 { margin-bottom: 1.5rem; }
    .mt-2 { margin-top: 0.5rem; } .mt-3 { margin-top: 0.75rem; } .mt-4 { margin-top: 1rem; } .mt-6 { margin-top: 1.5rem; }
    @media print { .page-break { page-break-before: always; } .module-nav { display: none; } }
    @media (max-width: 768px) { .hero { padding: 1.5rem 1rem; } .hero h1 { font-size: 1.5rem; } .metric-grid { grid-template-columns: repeat(3, 1fr); } .max-w { padding: 0 1rem; } }
</style>
"""


# ================================================================
# Main render function
# ================================================================

def render_10module_html(
    agent_outputs: Dict[str, dict],
    report_meta: Optional[dict] = None,
    language: str = "zh",
) -> str:
    """Render the full 10-module Initiating Coverage report."""
    meta = report_meta or {}
    outputs = agent_outputs or {}
    lang = language if language in ("zh", "en") else "zh"

    editor = outputs.get('editor', {})
    thesis = outputs.get('investment_thesis', {})
    rating_box = thesis.get('rating_box', {})
    rating = rating_box.get('rating', editor.get('final_rating', _na(lang)))
    target_price = rating_box.get('target_price', editor.get('final_target_price', meta.get('target_price', _na(lang))))
    share_price = meta.get('share_price', rating_box.get('current_price', _na(lang)))
    tagline = editor.get('tagline', meta.get('tagline', ''))

    company = meta.get('company_name', 'Company')
    ticker = meta.get('company_ticker', 'TICK')
    sector = meta.get('sector', 'Technology')
    report_date = meta.get('report_date', datetime.now().strftime('%Y年%m月'))

    # Build HTML
    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company} ({ticker}) — {T("initiating_coverage", lang)}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    {CSS_STYLES}
</head>
<body>

<div class="hero">
    <div class="max-w">
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
            <span style="background:rgba(99,102,241,0.2);color:#a5b4fc;padding:0.2rem 0.75rem;border-radius:9999px;font-size:0.75rem;font-weight:500;letter-spacing:0.05em;">{T("initiating_coverage", lang)}</span>
            <span style="color:#64748b;font-size:0.8rem;">{report_date}</span>
        </div>
        <h1>{company}</h1>
        <div style="display:flex;align-items:center;gap:0.75rem;margin:0.75rem 0 1.5rem;">
            <span class="ticker">{ticker}</span>
            <span class="sector">{sector}</span>
        </div>
        <div style="display:flex;align-items:flex-end;gap:2rem;flex-wrap:wrap;">
            <div><span class="price-label">{T("rating", lang)}</span>{_rating_badge(rating, lang)}</div>
            <div><span class="price-label">{T("price", lang)}</span><p class="price">{share_price}</p></div>
            <div><span class="price-label">{T("target_12m", lang)}</span><p class="target">{target_price}</p></div>
        </div>
    </div>
</div>

<div class="module-nav">
    <div class="max-w" style="display:flex;flex-wrap:wrap;gap:0.25rem;">
        <a href="#m1">{T("m1_title", lang)}</a><a href="#m2">{T("m2_title", lang)}</a>
        <a href="#m3">{T("m3_title", lang)}</a><a href="#m4">{T("m4_title", lang)}</a>
        <a href="#m5">{T("m5_title", lang)}</a><a href="#m6">{T("m6_title", lang)}</a>
        <a href="#m7">{T("m7_title", lang)}</a><a href="#m8">{T("m8_title", lang)}</a>
        <a href="#m9">{T("m9_title", lang)}</a><a href="#m10">{T("m10_title", lang)}</a>
    </div>
</div>

<div class="max-w">

<div class="highlight-box" style="margin-top:1.5rem;">
    <p class="body font-medium">{tagline or _na(lang)}</p>
</div>
'''

    modules = [
        ('m1', T("m1_title", lang), _render_module_1_investment_thesis, 'investment_thesis'),
        ('m2', T("m2_title", lang), _render_module_2_investment_rationale, 'investment_rationale'),
        ('m3', T("m3_title", lang), _render_module_3_industry_analysis, 'industry_analysis'),
        ('m4', T("m4_title", lang), _render_module_4_company_analysis, 'company_analysis'),
        ('m5', T("m5_title", lang), _render_module_5_financial_analysis, 'financial_analysis'),
        ('m6', T("m6_title", lang), _render_module_6_earnings_forecast, 'earnings_forecast'),
        ('m7', T("m7_title", lang), _render_module_7_valuation_analysis, 'valuation_analysis'),
        ('m8', T("m8_title", lang), _render_module_8_technical_analysis, 'technical_analysis'),
        ('m9', T("m9_title", lang), _render_module_9_monitor_signals, 'monitor_signals'),
        ('m10', T("m10_title", lang), _render_module_10_risk_disclosure, 'risk_disclosure'),
    ]

    for anchor, title, renderer, key in modules:
        html += f'<section class="section page-break" id="{anchor}"><h2 class="section-title">{title}</h2>{renderer(outputs.get(key, {}), lang)}</section>\n'

    overall = editor.get('overall_assessment', '')
    if overall:
        html += f'<section class="section"><h2 class="section-title">{T("overall_assessment", lang)}</h2><div class="highlight-box"><p class="body font-medium">{overall}</p></div></section>\n'

    disc = T("disclaimer", lang)
    source = meta.get('research_source', 'SanSi AI Equity Research')
    data_src = meta.get('data_source_text', 'Company Filings, FMP API')
    gen_time = datetime.now().strftime('%Y-%m-%d %H:%M')

    html += f'''
<div class="disclaimer">
    <p style="margin-bottom:0.25rem;"><strong>{T("powered_by", lang)}</strong> | {source}</p>
    <p>{disc}</p>
    <p style="margin-top:0.5rem;">Data: {data_src} &middot; Generated: {gen_time}</p>
</div>
</div>
</body>
</html>'''

    return html


def render_from_json_dir(json_dir: str, report_meta: dict = None, language: str = "zh") -> str:
    """Load agent JSONs from directory and render."""
    import os
    agent_outputs = {}
    for name in ['investment_thesis','investment_rationale','industry_analysis','company_analysis',
                  'financial_analysis','earnings_forecast','valuation_analysis','technical_analysis',
                  'monitor_signals','risk_disclosure','editor']:
        path = os.path.join(json_dir, f'{name}.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                agent_outputs[name] = json.load(f)
        else:
            agent_outputs[name] = {}
    return render_10module_html(agent_outputs, report_meta, language)
