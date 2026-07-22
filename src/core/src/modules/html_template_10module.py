"""
10-Module Professional HTML Report Renderer.

Renders the full 10-module Initiating Coverage report from agent JSON outputs,
following the equity_research_template.md structure exactly.

Usage:
    render_10module_html(report_data) -> str  (full HTML page)
"""

import json
import re as _re
from datetime import datetime
from typing import Dict, Any, Optional


# ================================================================
# Markdown → HTML helpers
# ================================================================

def _md_to_html(text: str) -> str:
    """Convert markdown to HTML with bold, lists, headings."""
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
            if in_list:
                out.append('</ul>'); in_list = False
            c = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[4:])
            out.append(f'<h4 class="h4">{c}</h4>')
            continue
        if s.startswith('## '):
            if in_list:
                out.append('</ul>'); in_list = False
            c = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[3:])
            out.append(f'<h3 class="h3">{c}</h3>')
            continue
        if s.startswith('- '):
            if not in_list:
                out.append('<ul class="ulist">'); in_list = True
            item = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s[2:])
            out.append(f'<li>{item}</li>')
            continue
        if in_list:
            out.append('</ul>'); in_list = False
        c = _re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
        out.append(f'<p class="body">{c}</p>')
    if in_list:
        out.append('</ul>')
    return '\n'.join(out)


def _auto_bold_numbers(text: str) -> str:
    """Bold monetary amounts and percentages in HTML."""
    if not text or '<strong>' in text:
        return text
    text = _re.sub(r'(\$[\d,.]+\s*(?:billion|million|trillion|bn|mn|trn|B|M|K|T))',
                   r'<strong>\1</strong>', text, flags=_re.IGNORECASE)
    text = _re.sub(r'(?<!\d)([\-+]?\d+\.?\d*%)', r'<strong>\1</strong>', text)
    text = _re.sub(r'\b(\d+\.?\d*x)\b', r'<strong>\1</strong>', text)
    return text


def _safe_get(d: dict, key: str, default: Any = "N/A") -> Any:
    """Safe dict access for nested agent output."""
    if not isinstance(d, dict):
        return default
    return d.get(key, default)


def _grid_card(label: str, value: str, accent: str = "#6366f1") -> str:
    return f'''<div class="metric-card" style="--accent:{accent};">
        <span class="metric-label">{label}</span>
        <span class="metric-value">{value}</span></div>'''


def _rating_badge(rating: str) -> str:
    r = str(rating).strip().lower()
    if r in ('buy', 'outperform', 'overweight', 'strong buy', '买入', '增持'):
        cls = 'badge-buy'
    elif r in ('sell', 'underperform', 'underweight', 'strong sell', '减持'):
        cls = 'badge-sell'
    else:
        cls = 'badge-hold'
    return f'<span class="rating-badge {cls}">{rating}</span>'


def _positive_negative_badge(text: str) -> str:
    t = str(text).lower()
    if any(w in t for w in ('positive', 'bullish', '正面', '利好')):
        return '<span class="badge-positive">Positive</span>'
    elif any(w in t for w in ('negative', 'bearish', '负面', '利空')):
        return '<span class="badge-negative">Negative</span>'
    return '<span class="badge-neutral">Neutral</span>'


def _prob_badge(prob: str) -> str:
    p = str(prob).lower()
    if '高' in p or p == 'high':
        return '<span class="badge-high">High</span>'
    elif '中' in p or p == 'medium':
        return '<span class="badge-med">Medium</span>'
    return '<span class="badge-low">Low</span>'


def _impact_badge(impact: str) -> str:
    p = str(impact).lower()
    if '重大' in p or p == 'significant':
        return '<span class="badge-high">Significant</span>'
    elif '中等' in p or p == 'moderate':
        return '<span class="badge-med">Moderate</span>'
    return '<span class="badge-low">Limited</span>'


# ================================================================
# Module renderers — each renders one agent's output to HTML
# ================================================================

def _render_module_1_investment_thesis(data: dict) -> str:
    """模块一：投资概要"""
    if not data:
        return '<p class="body muted">Investment thesis not available.</p>'

    rb = data.get('rating_box', {})
    theses = data.get('core_theses', [])
    snap = data.get('financial_snapshot', {})
    summary = data.get('executive_summary', '')

    html = ''

    # Rating box table
    html += '<table class="data-table mb-6"><thead><tr><th>Item</th><th>Content</th></tr></thead><tbody>'
    for key, label in [('rating', 'Rating'), ('current_price', 'Current Price'),
                        ('target_price', 'Target Price'), ('week_52_range', '52-Week Range'),
                        ('total_market_cap', 'Market Cap'), ('float_market_cap', 'Float Market Cap')]:
        html += f'<tr><td class="font-semibold">{label}</td><td>{_safe_get(rb, key)}</td></tr>'
    html += '</tbody></table>'

    # Core theses
    if theses:
        html += '<h3 class="h3">Core Investment Theses</h3>'
        for i, t in enumerate(theses, 1):
            title = t.get('thesis_title', '')
            exp = t.get('expansion', '')
            html += f'''<div class="highlight-box">
                <p class="thesis-title">Thesis {i}: {title}</p>
                <p class="body">{exp}</p></div>'''

    # Financial snapshot table
    years = snap.get('years', [])
    if years:
        html += '<h3 class="h3">Financial & Valuation Snapshot</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Metric</th>'
        for y in years:
            html += f'<th>{y}</th>'
        html += '</tr></thead><tbody>'
        rows = [
            ('Revenue', 'revenue'), ('Revenue Growth', 'revenue_growth'),
            ('Net Income', 'net_income'), ('Net Income Growth', 'net_income_growth'),
            ('Gross Margin', 'gross_margin'), ('EBITDA Margin', 'ebitda_margin'),
            ('ROE', 'roe'), ('EPS', 'eps'), ('PE (x)', 'pe'),
            ('PB (x)', 'pb'), ('EV/EBITDA (x)', 'ev_ebitda'), ('Dividend Yield', 'dividend_yield'),
        ]
        for label, key in rows:
            vals = snap.get(key, [])
            html += f'<tr><td class="font-semibold">{label}</td>'
            for v in vals:
                html += f'<td>{v}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'

    # Executive summary
    if summary:
        html += f'<div class="highlight-box mt-6"><p class="body font-medium">{summary}</p></div>'

    return html


def _render_module_2_investment_rationale(data: dict) -> str:
    """模块二：投资逻辑与风险"""
    if not data:
        return '<p class="body muted">Investment rationale not available.</p>'

    html = ''

    pillars = data.get('pillars', [])
    if pillars:
        html += '<h3 class="section-subtitle">Investment Pillars</h3>'
        for i, p in enumerate(pillars, 1):
            html += f'''<div class="content-card mb-4">
                <h4 class="h4" style="color:#6366f1;">Pillar {i}: {p.get("pillar_title", "")}</h4>
                <div class="pillar-block"><strong>Market Opportunity:</strong> {_md_to_html(p.get("market_opportunity", ""))}</div>
                <div class="pillar-block"><strong>Competitive Advantage:</strong> {_md_to_html(p.get("competitive_advantage", ""))}</div>
                <div class="pillar-block"><strong>Financial Impact:</strong> {_md_to_html(p.get("financial_impact", ""))}</div>
            </div>'''

    # Company-specific risks
    company_risks = data.get('company_risks', [])
    if company_risks:
        html += '<h3 class="section-subtitle">Company-Specific Risks</h3>'
        for r in company_risks:
            html += f'''<div class="risk-item">
                <p><strong>{r.get("risk_title", "")}</strong> {_prob_badge(r.get("probability",""))} {_impact_badge(r.get("impact",""))}</p>
                <p class="body">{r.get("description", "")}</p>
                <p class="body text-sm muted">Mitigation: {r.get("mitigation", "N/A")}</p></div>'''

    # Industry risks
    industry_risks = data.get('industry_risks', [])
    if industry_risks:
        html += '<h3 class="section-subtitle">Industry & Market Risks</h3>'
        for r in industry_risks:
            html += f'''<div class="risk-item">
                <p><strong>{r.get("risk_title", "")}</strong> {_prob_badge(r.get("probability",""))} {_impact_badge(r.get("impact",""))}</p>
                <p class="body">{r.get("description", "")}</p></div>'''

    kt = data.get('key_takeaway', '')
    if kt:
        html += f'<div class="highlight-box mt-4"><p class="body font-medium">{kt}</p></div>'

    return html


def _render_module_3_industry_analysis(data: dict) -> str:
    """模块三：行业分析"""
    if not data:
        return '<p class="body muted">Industry analysis not available.</p>'

    html = ''

    # Market overview
    mo = data.get('market_overview', {})
    if mo:
        html += '<h3 class="section-subtitle">Industry Definition & Market Size</h3>'
        html += f'''<div class="content-card">
            <p class="body"><strong>Industry:</strong> {_safe_get(mo, "industry_name")}</p>
            <p class="body"><strong>Boundary:</strong> {_safe_get(mo, "industry_boundary")}</p>
            <p class="body"><strong>Global Market Size:</strong> {_safe_get(mo, "market_size_global")}</p>
            <p class="body"><strong>Historical CAGR:</strong> {_safe_get(mo, "historical_cagr_3_5yr")} |
               <strong>Forecast CAGR:</strong> {_safe_get(mo, "forecast_cagr_3_5yr")}</p>
            <p class="body"><strong>Lifecycle Stage:</strong> {_safe_get(mo, "lifecycle_stage")}</p>
            <p class="body text-sm muted">{_safe_get(mo, "lifecycle_rationale")}</p></div>'''

    # Industry chain
    ic = data.get('industry_chain', {})
    if ic:
        html += '<h3 class="section-subtitle">Industry Chain Analysis</h3>'
        html += f'''<div class="content-card">
            <p class="body">{_safe_get(ic, "chain_description")}</p>
            <p class="body"><strong>Value Distribution:</strong> {_safe_get(ic, "value_distribution")}</p>
            <p class="body"><strong>Company Position:</strong> {_safe_get(ic, "company_position")}</p></div>'''

    # Competitive landscape
    cl = data.get('competitive_landscape', {})
    if cl:
        html += '<h3 class="section-subtitle">Competitive Landscape</h3>'
        html += f'<p class="body"><strong>Concentration:</strong> {_safe_get(cl, "concentration")} | <strong>Intensity:</strong> {_safe_get(cl, "competition_intensity")}</p>'
        html += f'<p class="body"><strong>Company Rank:</strong> {_safe_get(cl, "company_rank")}</p>'

        competitors = cl.get('competitors', [])
        if competitors:
            html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Company</th><th>Revenue</th><th>Rev Growth</th><th>Gross Margin</th><th>ROE</th><th>PE</th><th>PB</th><th>Market Cap</th></tr></thead><tbody>'
            for c in competitors:
                html += f'<tr><td class="font-semibold">{c.get("company_name","")}</td><td>{c.get("revenue","")}</td><td>{c.get("revenue_growth","")}</td><td>{c.get("gross_margin","")}</td><td>{c.get("roe","")}</td><td>{c.get("pe","")}</td><td>{c.get("pb","")}</td><td>{c.get("market_cap","")}</td></tr>'
            ia = cl.get('industry_average', {})
            if ia.get('company_name'):
                html += f'<tr class="font-semibold bg-slate-50"><td>{ia.get("company_name","")}</td><td>{ia.get("revenue","")}</td><td>{ia.get("revenue_growth","")}</td><td>{ia.get("gross_margin","")}</td><td>{ia.get("roe","")}</td><td>{ia.get("pe","")}</td><td>{ia.get("pb","")}</td><td>{ia.get("market_cap","")}</td></tr>'
            html += '</tbody></table></div>'

    # Porter's Five Forces
    pf = data.get('porter_five_forces', {})
    if pf:
        html += '<h3 class="section-subtitle">Porter\'s Five Forces</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Force</th><th>Intensity</th><th>Analysis</th></tr></thead><tbody>'
        forces = [
            ('Threat of New Entrants', 'threat_new_entrants'),
            ('Supplier Power', 'supplier_power'),
            ('Buyer Power', 'buyer_power'),
            ('Threat of Substitutes', 'threat_substitutes'),
            ('Industry Rivalry', 'rivalry'),
        ]
        for label, key in forces:
            val = _safe_get(pf, key, 'N/A')
            html += f'<tr><td class="font-semibold">{label}</td><td>{val}</td><td>{val}</td></tr>'
        html += '</tbody></table></div>'

    # Trends
    trends = data.get('trends', [])
    if trends:
        html += '<h3 class="section-subtitle">Key Industry Trends</h3>'
        for t in trends:
            html += f'''<div class="content-card mb-3">
                <h4 class="h4">{t.get("trend_name", "")}</h4>
                <p class="body">{t.get("description", "")}</p>
                <p class="body text-sm"><strong>Drivers:</strong> {t.get("drivers", "")}</p>
                <p class="body text-sm"><strong>Impact on Company:</strong> {t.get("impact_on_company", "")}</p>
                <p class="body text-sm"><strong>Timeline:</strong> {t.get("timeline", "")}</p></div>'''

    kt = data.get('key_takeaway', '')
    if kt:
        html += f'<div class="highlight-box mt-4"><p class="body font-medium">{kt}</p></div>'

    return html


def _render_module_4_company_analysis(data: dict) -> str:
    """模块四：公司分析"""
    if not data:
        return '<p class="body muted">Company analysis not available.</p>'

    html = ''

    co = data.get('company_overview', {})
    if co:
        html += '<h3 class="section-subtitle">Company Overview</h3>'
        html += f'<p class="body"><strong>One-liner:</strong> {_safe_get(co, "one_liner")}</p>'
        html += f'<p class="body"><strong>Business Model:</strong> {_safe_get(co, "business_model")}</p>'
        html += f'<p class="body"><strong>Customers:</strong> {_safe_get(co, "customers")}</p>'
        html += f'<p class="body"><strong>Scale:</strong> {_safe_get(co, "scale")}</p>'
        html += f'<p class="body"><strong>Ownership:</strong> {_safe_get(co, "ownership")}</p>'

    # Milestones
    milestones = data.get('milestones', [])
    if milestones:
        html += '<h3 class="section-subtitle">Key Milestones</h3>'
        html += '<div class="timeline">'
        for m in milestones:
            html += f'''<div class="timeline-item">
                <span class="timeline-year">{m.get("year","")}</span>
                <span>{m.get("event","")}</span></div>'''
        html += '</div>'

    # Management
    execs = data.get('executives', [])
    if execs:
        html += '<h3 class="section-subtitle">Management Team</h3>'
        for e in execs:
            html += f'''<div class="content-card mb-3">
                <h4 class="h4">{e.get("name","")} — {e.get("title","")} (since {e.get("tenure","")})</h4>
                <p class="body">{e.get("background","")}</p>
                <p class="body text-sm muted">Shareholding: {e.get("shareholding","N/A")}</p></div>'''

    # Governance
    gov = data.get('governance', {})
    if gov and gov.get('board_structure'):
        html += '<h3 class="section-subtitle">Governance</h3>'
        html += f'<p class="body"><strong>Board:</strong> {_safe_get(gov, "board_structure")}</p>'
        html += f'<p class="body"><strong>Equity Incentives:</strong> {_safe_get(gov, "equity_incentives")}</p>'
        html += f'<p class="body"><strong>Dividend History:</strong> {_safe_get(gov, "dividend_history")}</p>'
        html += f'<p class="body"><strong>Related Party:</strong> {_safe_get(gov, "related_party")}</p>'

    # Business segments
    segments = data.get('business_segments', [])
    if segments:
        html += '<h3 class="section-subtitle">Business Segment Breakdown</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Segment</th><th>Revenue</th><th>Share</th><th>YoY Growth</th><th>Gross Margin</th><th>Key Driver</th></tr></thead><tbody>'
        for s in segments:
            html += f'<tr><td class="font-semibold">{s.get("name","")}</td><td>{s.get("revenue","")}</td><td>{s.get("revenue_share","")}</td><td>{s.get("yoy_growth","")}</td><td>{s.get("gross_margin","")}</td><td>{s.get("key_driver","")}</td></tr>'
        html += '</tbody></table></div>'

    # Moat
    moat = data.get('moat_analysis', {})
    if moat:
        html += '<h3 class="section-subtitle">Competitive Moat Analysis</h3>'
        html += f'<p class="body"><strong>Overall Rating:</strong> {_safe_get(moat, "overall_moat_rating")}</p>'
        for dim, label in [('brand_barrier', 'Brand/License'), ('tech_barrier', 'Technology/Patents'),
                           ('channel_barrier', 'Channel/Network'), ('scale_barrier', 'Scale/Cost'),
                           ('switching_cost', 'Switching Cost')]:
            v = moat.get(dim, '')
            if v:
                html += f'<p class="body"><strong>{label}:</strong> {v}</p>'

    # Growth drivers
    short = data.get('short_term_drivers', [])
    medium = data.get('medium_term_drivers', [])
    if short or medium:
        html += '<h3 class="section-subtitle">Growth Drivers</h3>'
        if short:
            html += '<h4 class="h4">Short-term (1-2 years)</h4>'
            for d in short:
                html += f'''<div class="content-card mb-2"><p class="body"><strong>{d.get("driver_name","")}</strong></p>
                    <p class="body text-sm">Current: {d.get("current_status","")} → Opportunity: {d.get("incremental_opportunity","")}</p>
                    <p class="body text-sm muted">Timeline: {d.get("timeline","")}</p></div>'''
        if medium:
            html += '<h4 class="h4">Medium-term (3-5 years)</h4>'
            for d in medium:
                html += f'''<div class="content-card mb-2"><p class="body"><strong>{d.get("driver_name","")}</strong></p>
                    <p class="body text-sm">Current: {d.get("current_status","")} → Opportunity: {d.get("incremental_opportunity","")}</p>
                    <p class="body text-sm muted">Timeline: {d.get("timeline","")}</p></div>'''

    # Customer analysis
    ca = data.get('customer_analysis', {})
    if ca and ca.get('customer_segments'):
        html += '<h3 class="section-subtitle">Customer & Channel Analysis</h3>'
        html += f'<p class="body"><strong>Segments:</strong> {_safe_get(ca, "customer_segments")}</p>'
        html += f'<p class="body"><strong>Top 5 Concentration:</strong> {_safe_get(ca, "top5_concentration")}</p>'
        html += f'<p class="body"><strong>CAC/LTV:</strong> {_safe_get(ca, "cac_ltv")}</p>'
        html += f'<p class="body"><strong>Retention:</strong> {_safe_get(ca, "retention")}</p>'
        html += f'<p class="body"><strong>Channel Mix:</strong> {_safe_get(ca, "channel_mix")}</p>'

    return html


def _render_module_5_financial_analysis(data: dict) -> str:
    """模块五：财务分析"""
    if not data:
        return '<p class="body muted">Financial analysis not available.</p>'

    html = ''

    # Revenue
    ra = data.get('revenue_analysis', {})
    if ra:
        html += '<h3 class="section-subtitle">Revenue Analysis</h3>'
        html += f'<p class="body">{_safe_get(ra, "revenue_trend")}</p>'
        html += f'<p class="body">{_safe_get(ra, "revenue_mix_change")}</p>'
        html += f'<p class="body"><strong>Growth Driver:</strong> {_safe_get(ra, "volume_vs_price")}</p>'

    # Profitability
    pa = data.get('profitability_analysis', {})
    if pa:
        html += '<h3 class="section-subtitle">Profitability Analysis</h3>'
        tbl = pa.get('table', {})
        years = tbl.get('years', [])
        if years:
            html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Metric</th>'
            for y in years:
                html += f'<th>{y}</th>'
            html += '</tr></thead><tbody>'
            for label, key in [('Gross Margin', 'gross_margin'), ('EBITDA Margin', 'ebitda_margin'),
                                ('Net Margin', 'net_margin'), ('ROE', 'roe'), ('ROA', 'roa'), ('EPS', 'eps')]:
                html += f'<tr><td class="font-semibold">{label}</td>'
                for v in tbl.get(key, []):
                    html += f'<td>{v}</td>'
                html += '</tr>'
            html += '</tbody></table></div>'
        html += f'<p class="body">{_safe_get(pa, "margin_attribution")}</p>'
        html += f'<p class="body">{_safe_get(pa, "roe_drivers")}</p>'

    # DuPont
    dup = data.get('dupont_analysis', {})
    if dup:
        html += '<h3 class="section-subtitle">DuPont Analysis</h3>'
        dyears = dup.get('years', [])
        if dyears:
            html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Component</th>'
            for y in dyears:
                html += f'<th>{y}</th>'
            html += '</tr></thead><tbody>'
            for label, key in [('ROE', 'roe_values'), ('= Net Margin', 'net_margin_values'),
                                ('x Asset Turnover', 'asset_turnover_values'),
                                ('x Equity Multiplier', 'equity_multiplier_values')]:
                html += f'<tr><td class="font-semibold">{label}</td>'
                for v in dup.get(key, []):
                    html += f'<td>{v}</td>'
                html += '</tr>'
            html += '</tbody></table></div>'
        html += f'<p class="body"><strong>Conclusion:</strong> {_safe_get(dup, "driver_conclusion")}</p>'

    # Operating efficiency
    oe = data.get('operating_efficiency', {})
    if oe:
        html += '<h3 class="section-subtitle">Operating Efficiency</h3>'
        html += f'<p class="body">{_safe_get(oe, "analysis")}</p>'

    # Cash flow
    cf = data.get('cash_flow_analysis', {})
    if cf:
        html += '<h3 class="section-subtitle">Cash Flow Analysis</h3>'
        html += f'<p class="body"><strong>Health:</strong> {_safe_get(cf, "health_assessment")}</p>'
        html += f'<p class="body"><strong>Coverage:</strong> {_safe_get(cf, "coverage_assessment")}</p>'

    # Credit
    cm = data.get('credit_metrics', {})
    if cm:
        html += '<h3 class="section-subtitle">Credit & Capital Structure</h3>'
        html += f'<p class="body"><strong>Assessment:</strong> {_safe_get(cm, "overall_assessment")}</p>'

    # Industry KPIs
    ik = data.get('industry_kpis', {})
    kpis = ik.get('kpis', [])
    if kpis:
        html += f'<h3 class="section-subtitle">Industry-Specific KPIs ({_safe_get(ik, "industry_type")})</h3>'
        for k in kpis:
            html += f'<p class="body"><strong>{k.get("name","")}:</strong> {k.get("value","")} — {k.get("interpretation","")}</p>'

    kt = data.get('key_takeaway', '')
    if kt:
        html += f'<div class="highlight-box mt-4"><p class="body font-medium">{kt}</p></div>'

    return html


def _render_module_6_earnings_forecast(data: dict) -> str:
    """模块六：盈利预测"""
    if not data:
        return '<p class="body muted">Earnings forecast not available.</p>'

    html = ''

    # Assumptions
    assumptions = data.get('assumptions', [])
    if assumptions:
        html += '<h3 class="section-subtitle">Core Assumptions</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Parameter</th><th>2025E</th><th>2026E</th><th>2027E</th><th>Rationale</th></tr></thead><tbody>'
        for a in assumptions:
            html += f'<tr><td class="font-semibold">{a.get("parameter","")}</td><td>{a.get("value_2025e","")}</td><td>{a.get("value_2026e","")}</td><td>{a.get("value_2027e","")}</td><td class="text-sm">{a.get("rationale","")}</td></tr>'
        html += '</tbody></table></div>'

    # Forecast income statement
    ist = data.get('income_statement', {})
    items = ist.get('line_items', [])
    v25 = ist.get('values_2025e', [])
    v26 = ist.get('values_2026e', [])
    v27 = ist.get('values_2027e', [])
    if items:
        html += '<h3 class="section-subtitle">Forecast Income Statement</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Line Item</th><th>2025E</th><th>2026E</th><th>2027E</th></tr></thead><tbody>'
        for i, item in enumerate(items):
            html += f'<tr><td class="font-semibold">{item}</td><td>{v25[i] if i < len(v25) else "N/A"}</td><td>{v26[i] if i < len(v26) else "N/A"}</td><td>{v27[i] if i < len(v27) else "N/A"}</td></tr>'
        html += '</tbody></table></div>'

    # Three scenarios
    scenarios = data.get('scenarios', [])
    if scenarios:
        html += '<h3 class="section-subtitle">Scenario Analysis</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Scenario</th><th>Assumptions</th><th>2025E Revenue</th><th>2025E EPS</th><th>Target Price</th><th>Probability</th></tr></thead><tbody>'
        for s in scenarios:
            html += f'<tr><td class="font-semibold">{s.get("name","")}</td><td class="text-sm">{s.get("assumptions","")}</td><td>{s.get("revenue_2025e","")}</td><td>{s.get("eps_2025e","")}</td><td>{s.get("target_price","")}</td><td>{s.get("probability","")}</td></tr>'
        html += '</tbody></table></div>'

    kt = data.get('key_takeaway', '')
    if kt:
        html += f'<div class="highlight-box mt-4"><p class="body font-medium">{kt}</p></div>'

    return html


def _render_module_7_valuation_analysis(data: dict) -> str:
    """模块七：估值分析"""
    if not data:
        return '<p class="body muted">Valuation analysis not available.</p>'

    html = ''

    # DCF
    dcf = data.get('dcf_analysis', {})
    if dcf:
        html += '<h3 class="section-subtitle">DCF Valuation</h3>'
        html += f'<p class="body"><strong>Target Price:</strong> {_safe_get(dcf, "target_price")} (Range: {_safe_get(dcf, "low_estimate")} – {_safe_get(dcf, "high_estimate")})</p>'
        assumptions = dcf.get('assumptions', [])
        if assumptions:
            html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Parameter</th><th>Value</th><th>Rationale</th></tr></thead><tbody>'
            for a in assumptions:
                html += f'<tr><td class="font-semibold">{a.get("parameter","")}</td><td>{a.get("value","")}</td><td class="text-sm">{a.get("rationale","")}</td></tr>'
            html += '</tbody></table></div>'
        html += f'<p class="body text-sm muted">{_safe_get(dcf, "sensitivity_note")}</p>'

    # Peer comparison
    pc = data.get('peer_comparison', {})
    if pc:
        html += '<h3 class="section-subtitle">Peer Comparison</h3>'
        html += f'<p class="body text-sm muted"><strong>Selection Criteria:</strong> {_safe_get(pc, "selection_rationale")}</p>'
        peers = pc.get('peers', [])
        if peers:
            html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Company</th><th>Market Cap</th><th>PE(TTM)</th><th>PE(2025E)</th><th>PE(2026E)</th><th>PB</th><th>EV/EBITDA</th><th>ROE</th><th>Rev Growth</th><th>Div Yield</th></tr></thead><tbody>'
            # Target company first
            tc = pc.get('target_company', {})
            if tc.get('company_name'):
                html += f'<tr class="font-semibold bg-indigo-50"><td>{tc.get("company_name","")}</td><td>{tc.get("market_cap","")}</td><td>{tc.get("pe_ttm","")}</td><td>{tc.get("pe_2025e","")}</td><td>{tc.get("pe_2026e","")}</td><td>{tc.get("pb","")}</td><td>{tc.get("ev_ebitda","")}</td><td>{tc.get("roe","")}</td><td>{tc.get("revenue_growth","")}</td><td>{tc.get("dividend_yield","")}</td></tr>'
            for p in peers:
                html += f'<tr><td>{p.get("company_name","")}</td><td>{p.get("market_cap","")}</td><td>{p.get("pe_ttm","")}</td><td>{p.get("pe_2025e","")}</td><td>{p.get("pe_2026e","")}</td><td>{p.get("pb","")}</td><td>{p.get("ev_ebitda","")}</td><td>{p.get("roe","")}</td><td>{p.get("revenue_growth","")}</td><td>{p.get("dividend_yield","")}</td></tr>'
            # Summary stats
            for row_key, label in [('max_values', 'Maximum'), ('percentile_75', '75th Pct'), ('median', 'Median'), ('percentile_25', '25th Pct'), ('min_values', 'Minimum')]:
                row = pc.get(row_key, {})
                if row.get('company_name'):
                    html += f'<tr class="font-semibold bg-slate-50"><td>{label}</td><td>{row.get("market_cap","")}</td><td>{row.get("pe_ttm","")}</td><td>{row.get("pe_2025e","")}</td><td>{row.get("pe_2026e","")}</td><td>{row.get("pb","")}</td><td>{row.get("ev_ebitda","")}</td><td>{row.get("roe","")}</td><td>{row.get("revenue_growth","")}</td><td>{row.get("dividend_yield","")}</td></tr>'
            html += '</tbody></table></div>'

    # Historical range
    hr = data.get('historical_range', [])
    if hr:
        html += '<h3 class="section-subtitle">Historical Valuation Range</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Metric</th><th>Current</th><th>1Y %ile</th><th>3Y %ile</th><th>5Y %ile</th></tr></thead><tbody>'
        for h in hr:
            html += f'<tr><td class="font-semibold">{h.get("metric","")}</td><td>{h.get("current_value","")}</td><td>{h.get("percentile_1y","")}</td><td>{h.get("percentile_3y","")}</td><td>{h.get("percentile_5y","")}</td></tr>'
        html += '</tbody></table></div>'

    # Valuation summary (Football Field)
    vs = data.get('valuation_summary', [])
    if vs:
        html += '<h3 class="section-subtitle">Valuation Summary (Football Field)</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Method</th><th>Weight</th><th>Price Range</th><th>Weighted Price</th></tr></thead><tbody>'
        for v in vs:
            html += f'<tr><td class="font-semibold">{v.get("method","")}</td><td>{v.get("weight","")}</td><td>{v.get("price_range","")}</td><td>{v.get("weighted_price","")}</td></tr>'
        html += '</tbody></table></div>'

    # Rating
    rating = data.get('rating', {})
    if rating:
        html += '<h3 class="section-subtitle">Rating & Recommendation</h3>'
        html += f'''<div class="content-card" style="display:flex; flex-wrap:wrap; gap:1.5rem; align-items:center;">
            <div><span class="metric-label">Current Price</span><p class="metric-value">{_safe_get(rating, "current_price")}</p></div>
            <div><span class="metric-label">12M Target</span><p class="metric-value" style="color:#6366f1;">{_safe_get(rating, "target_price_12m")}</p></div>
            <div><span class="metric-label">Upside/Downside</span><p class="metric-value">{_safe_get(rating, "upside_pct")} / {_safe_get(rating, "downside_pct")}</p></div>
            <div>{_rating_badge(_safe_get(rating, "rating"))}</div></div>'''
        html += f'<p class="body mt-3"><strong>Key Catalysts:</strong> {_safe_get(rating, "catalysts")}</p>'
        html += f'<p class="body"><strong>Suitable Style:</strong> {_safe_get(rating, "suitable_style")} | <strong>Unsuitable:</strong> {_safe_get(rating, "unsuitable_style")}</p>'

    kt = data.get('key_takeaway', '')
    if kt:
        html += f'<div class="highlight-box mt-4"><p class="body font-medium">{kt}</p></div>'

    return html


def _render_module_8_technical_analysis(data: dict) -> str:
    """模块八：技术面分析"""
    if not data:
        return '<p class="body muted">Technical analysis not available.</p>'

    html = ''

    ta = data.get('trend_assessment', {})
    if ta:
        html += '<h3 class="section-subtitle">Trend Assessment</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Indicator</th><th>Value</th><th>Status</th></tr></thead><tbody>'
        for key, label in [('ma5', 'MA5'), ('ma20', 'MA20'), ('ma60', 'MA60'), ('ma120', 'MA120'), ('ma250', 'MA250')]:
            html += f'<tr><td class="font-semibold">{label}</td><td>{ta.get(key, "N/A")}</td><td>{ta.get(key+"_status", "N/A")}</td></tr>'
        html += f'<tr><td class="font-semibold">Arrangement</td><td colspan="2">{ta.get("arrangement", "N/A")}</td></tr>'
        html += '</tbody></table></div>'

    # Key levels
    kl = data.get('key_levels', [])
    if kl:
        html += '<h3 class="section-subtitle">Key Price Levels</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>Type</th><th>Price</th><th>Basis</th></tr></thead><tbody>'
        for l in kl:
            html += f'<tr><td class="font-semibold">{l.get("level_type","")}</td><td>{l.get("price","")}</td><td class="text-sm">{l.get("basis","")}</td></tr>'
        html += '</tbody></table></div>'

    # Momentum
    mom = data.get('momentum', {})
    if mom:
        html += '<h3 class="section-subtitle">Momentum & Volume</h3>'
        html += '<div class="content-card">'
        html += f'<p class="body"><strong>RSI(14):</strong> {_safe_get(mom, "rsi14")} — {_safe_get(mom, "rsi_interpretation")}</p>'
        html += f'<p class="body"><strong>MACD:</strong> {_safe_get(mom, "macd_status")}</p>'
        html += f'<p class="body"><strong>20-Day Return:</strong> {_safe_get(mom, "change_20d")} | <strong>60-Day:</strong> {_safe_get(mom, "change_60d")}</p>'
        html += f'<p class="body"><strong>Volume:</strong> {_safe_get(mom, "volume_signal")} (Ratio: {_safe_get(mom, "volume_ratio")})</p>'
        html += f'<p class="body"><strong>Bollinger Width:</strong> {_safe_get(mom, "bollinger_width")} | <strong>ATR(14):</strong> {_safe_get(mom, "atr14")}</p>'
        html += '</div>'

    # Summary
    ts = data.get('trend_summary', '')
    bt = data.get('bullish_trigger', '')
    bet = data.get('bearish_trigger', '')
    if ts:
        html += f'<div class="highlight-box mt-4"><p class="body font-medium"><strong>Summary:</strong> {ts}</p></div>'
    if bt:
        html += f'<div class="content-card mb-2" style="border-left:4px solid #10b981;"><p class="body"><strong>Bullish Trigger:</strong> {bt}</p></div>'
    if bet:
        html += f'<div class="content-card mb-2" style="border-left:4px solid #ef4444;"><p class="body"><strong>Bearish Trigger:</strong> {bet}</p></div>'

    return html


def _render_module_9_monitor_signals(data: dict) -> str:
    """模块九：后续关注信号"""
    if not data:
        return '<p class="body muted">Monitor signals not available.</p>'

    html = ''

    signals = data.get('signals', [])
    if signals:
        html += '<h3 class="section-subtitle">Key Monitor Signals</h3>'
        html += '<div class="table-wrap"><table class="data-table"><thead><tr><th>#</th><th>Signal</th><th>Observation Method</th><th>Positive Signal</th><th>Negative Signal</th></tr></thead><tbody>'
        for s in signals:
            html += f'<tr><td>{s.get("rank","")}</td><td class="font-semibold">{s.get("signal_name","")}</td><td class="text-sm">{s.get("observation_method","")}</td><td class="text-sm" style="color:#059669;">{s.get("positive_signal","")}</td><td class="text-sm" style="color:#dc2626;">{s.get("negative_signal","")}</td></tr>'
        html += '</tbody></table></div>'

    freq = data.get('monitoring_frequency', '')
    if freq:
        html += f'<p class="body text-sm muted">Recommended monitoring frequency: <strong>{freq}</strong></p>'

    return html


def _render_module_10_risk_disclosure(data: dict) -> str:
    """模块十：风险提示"""
    if not data:
        return '<p class="body muted">Risk disclosure not available.</p>'

    html = ''

    for category, title in [('macro_risks', 'Macro Risks'), ('industry_risks', 'Industry Risks'),
                              ('operational_risks', 'Operational Risks'), ('valuation_risks', 'Valuation Risks')]:
        risks = data.get(category, [])
        if risks:
            html += f'<h3 class="section-subtitle">{title}</h3>'
            for r in risks:
                html += f'''<div class="risk-item">
                    <p><strong>{r.get("risk_name", "")}</strong> {_prob_badge(r.get("probability",""))} {_impact_badge(r.get("impact",""))}</p>
                    <p class="body">{r.get("description", "")}</p>
                    <p class="body text-sm muted">Potential Impact: {r.get("potential_impact_detail", "")}</p>
                    <p class="body text-sm muted">Mitigation: {r.get("mitigation", "N/A")}</p></div>'''

    rs = data.get('risk_summary', '')
    if rs:
        html += f'<div class="highlight-box mt-4" style="border-left-color:#f59e0b;"><p class="body font-medium"><strong>Risk-Reward Summary:</strong> {rs}</p></div>'

    return html


# ================================================================
# Main template & renderer
# ================================================================

CSS_STYLES = """
<style>
    :root { --accent: #6366f1; --text: #0f172a; --muted: #64748b; --border: #e2e8f0; --bg-card: #f8fafc; }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', -apple-system, sans-serif; color: var(--text); background: #fff; line-height: 1.6; }
    .max-w { max-width: 960px; margin: 0 auto; padding: 0 1.5rem; }

    /* Header */
    .hero { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 2.5rem 2rem 1.5rem; }
    .hero h1 { color: #fff; font-size: 2rem; font-weight: 700; }
    .hero .ticker { background: #1e293b; border: 1px solid #334155; color: #94a3b8; padding: 0.2rem 0.6rem; border-radius: 0.375rem; font-size: 0.8rem; font-weight: 500; }
    .hero .sector { color: #94a3b8; font-size: 0.85rem; }
    .hero .price-label { color: #64748b; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 0.08em; }
    .hero .price { color: #fff; font-size: 1.5rem; font-weight: 700; }
    .hero .target { color: #a5b4fc; font-size: 1.5rem; font-weight: 700; }

    /* Rating badges */
    .rating-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.875rem; font-weight: 700; letter-spacing: 0.02em; }
    .badge-buy { background: #d1fae5; color: #065f46; }
    .badge-sell { background: #fee2e2; color: #991b1b; }
    .badge-hold { background: #fef3c7; color: #92400e; }
    .badge-positive { background: #d1fae5; color: #065f46; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }
    .badge-negative { background: #fee2e2; color: #991b1b; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }
    .badge-neutral { background: #f1f5f9; color: #475569; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }
    .badge-high { background: #fee2e2; color: #991b1b; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }
    .badge-med { background: #fef3c7; color: #92400e; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }
    .badge-low { background: #d1fae5; color: #065f46; font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 9999px; font-weight: 600; }

    /* Metric cards */
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.75rem; margin: 1.5rem 0; }
    .metric-card { background: #fff; border: 1px solid var(--border); border-radius: 0.75rem; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06); position: relative; overflow: hidden; }
    .metric-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--accent, #6366f1); }
    .metric-label { display: block; color: var(--muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem; }
    .metric-value { display: block; color: var(--text); font-size: 1rem; font-weight: 600; }

    /* Sections */
    .section { margin: 2.5rem 0; padding-top: 1rem; }
    .section-title { font-size: 1.4rem; font-weight: 700; color: var(--text); border-left: 4px solid var(--accent); padding-left: 0.75rem; margin-bottom: 1.5rem; }
    .section-subtitle { font-size: 1.1rem; font-weight: 600; color: #1e293b; margin: 1.5rem 0 0.75rem; }
    .h3 { font-size: 1rem; font-weight: 600; color: #0f172a; margin: 1rem 0 0.5rem; border-left: 3px solid var(--accent); padding-left: 0.6rem; }
    .h4 { font-size: 0.9rem; font-weight: 600; color: #334155; margin: 0.75rem 0 0.4rem; }

    /* Body text */
    .body { font-size: 0.875rem; color: #334155; line-height: 1.7; margin-bottom: 0.5rem; }
    .body a { color: var(--accent); }
    .muted { color: var(--muted); }
    .text-sm { font-size: 0.8rem; }
    .font-semibold { font-weight: 600; }
    .font-medium { font-weight: 500; }

    /* Highlight box */
    .highlight-box { background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%); border-left: 4px solid var(--accent); border-radius: 0.75rem; padding: 1.25rem 1.5rem; margin: 1rem 0; }
    .thesis-title { font-size: 0.95rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem; }

    /* Content card */
    .content-card { background: var(--bg-card); border-radius: 0.75rem; padding: 1.25rem; border: 1px solid var(--border); margin-bottom: 0.5rem; }
    .pillar-block { margin: 0.5rem 0; }
    .risk-item { background: #fff; border: 1px solid var(--border); border-radius: 0.5rem; padding: 0.75rem 1rem; margin-bottom: 0.5rem; }
    .risk-item:hover { border-color: #cbd5e1; }

    /* Timeline */
    .timeline { padding: 0.5rem 0; }
    .timeline-item { display: flex; gap: 1rem; padding: 0.4rem 0; font-size: 0.875rem; border-bottom: 1px solid #f1f5f9; }
    .timeline-year { font-weight: 700; color: var(--accent); min-width: 3.5rem; }

    /* Tables */
    .table-wrap { overflow-x: auto; margin: 0.75rem 0 1.25rem; }
    .data-table { width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.8rem; border-radius: 0.5rem; overflow: hidden; border: 1px solid var(--border); }
    .data-table th { background: #f1f5f9; color: #475569; padding: 0.6rem 0.75rem; text-align: left; font-weight: 600; font-size: 0.75rem; white-space: nowrap; }
    .data-table td { padding: 0.55rem 0.75rem; border-top: 1px solid #f1f5f9; white-space: nowrap; }
    .data-table tr:hover { background: #f8fafc; }
    .bg-slate-50 { background: #f8fafc !important; }
    .bg-indigo-50 { background: #eef2ff !important; }

    /* Lists */
    .ulist { list-style: none; padding-left: 0; margin: 0.35rem 0; }
    .ulist li { padding: 0.3rem 0 0.3rem 1.2rem; position: relative; font-size: 0.875rem; color: #334155; line-height: 1.6; }
    .ulist li::before { content: '›'; position: absolute; left: 0; color: var(--accent); font-weight: 700; font-size: 1.1rem; }

    /* Nav */
    .module-nav { background: #f8fafc; border-bottom: 1px solid var(--border); padding: 0.75rem 0; position: sticky; top: 0; z-index: 10; }
    .module-nav a { font-size: 0.75rem; color: var(--muted); text-decoration: none; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
    .module-nav a:hover { color: var(--accent); background: #eef2ff; }

    /* Disclaimer */
    .disclaimer { background: #f8fafc; padding: 1.5rem; border-radius: 0.75rem; margin-top: 3rem; color: #94a3b8; font-size: 0.65rem; line-height: 1.5; }

    .mb-2 { margin-bottom: 0.5rem; } .mb-3 { margin-bottom: 0.75rem; } .mb-4 { margin-bottom: 1rem; } .mb-6 { margin-bottom: 1.5rem; }
    .mt-2 { margin-top: 0.5rem; } .mt-3 { margin-top: 0.75rem; } .mt-4 { margin-top: 1rem; } .mt-6 { margin-top: 1.5rem; }
    .mr-4 { margin-right: 1rem; }

    @media print { .page-break { page-break-before: always; } .module-nav { display: none; } }
    @media (max-width: 768px) {
        .hero { padding: 1.5rem 1rem; }
        .hero h1 { font-size: 1.5rem; }
        .metric-grid { grid-template-columns: repeat(3, 1fr); }
        .max-w { padding: 0 1rem; }
    }
</style>
"""


def render_10module_html(
    agent_outputs: Dict[str, dict],
    report_meta: Optional[dict] = None,
) -> str:
    """
    Render the full 10-module Initiating Coverage report from agent JSON outputs.

    Args:
        agent_outputs: Dict mapping module_name → agent output dict.
            Expected keys: investment_thesis, investment_rationale, industry_analysis,
            company_analysis, financial_analysis, earnings_forecast, valuation_analysis,
            technical_analysis, monitor_signals, risk_disclosure, editor
        report_meta: Optional metadata dict with keys:
            company_name, company_ticker, sector, share_price, target_price, market_cap,
            report_date, research_source, disclaimer_text, data_source_text

    Returns:
        Complete HTML string
    """
    meta = report_meta or {}
    outputs = agent_outputs or {}

    # Extract editor output for tagline, rating, summary
    editor = outputs.get('editor', {})
    thesis = outputs.get('investment_thesis', {})

    # Determine rating and colors
    rating_box = thesis.get('rating_box', {})
    rating = rating_box.get('rating', editor.get('final_rating', 'N/A'))
    target_price = rating_box.get('target_price', editor.get('final_target_price', meta.get('target_price', 'N/A')))
    share_price = meta.get('share_price', rating_box.get('current_price', 'N/A'))
    rating_color_class = _get_rating_class(rating)
    tagline = editor.get('tagline', meta.get('tagline', ''))

    report_date = meta.get('report_date', datetime.now().strftime('%B %Y'))
    ticker = meta.get('company_ticker', 'TICK')
    company = meta.get('company_name', 'Company')
    sector = meta.get('sector', 'Technology')

    # Build HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{company} ({ticker}) — Initiating Coverage</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    {CSS_STYLES}
</head>
<body>

<!-- Hero Header -->
<div class="hero">
    <div class="max-w">
        <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:1rem;">
            <span style="background:rgba(99,102,241,0.2); color:#a5b4fc; padding:0.2rem 0.75rem; border-radius:9999px; font-size:0.75rem; font-weight:500; letter-spacing:0.05em;">INITIATING COVERAGE</span>
            <span style="color:#64748b; font-size:0.8rem;">{report_date}</span>
        </div>
        <h1>{company}</h1>
        <div style="display:flex; align-items:center; gap:0.75rem; margin:0.75rem 0 1.5rem;">
            <span class="ticker">{ticker}</span>
            <span class="sector">{sector}</span>
        </div>
        <div style="display:flex; align-items:flex-end; gap:2rem; flex-wrap:wrap;">
            <div>
                <span class="price-label">Rating</span>
                {_rating_badge(rating)}
            </div>
            <div>
                <span class="price-label">Price</span>
                <p class="price">{share_price}</p>
            </div>
            <div>
                <span class="price-label">12M Target</span>
                <p class="target">{target_price}</p>
            </div>
        </div>
    </div>
</div>

<!-- Module Navigation -->
<div class="module-nav">
    <div class="max-w" style="display:flex; flex-wrap:wrap; gap:0.25rem;">
        <a href="#m1">1. Investment Thesis</a>
        <a href="#m2">2. Investment Rationale</a>
        <a href="#m3">3. Industry Analysis</a>
        <a href="#m4">4. Company Analysis</a>
        <a href="#m5">5. Financial Analysis</a>
        <a href="#m6">6. Earnings Forecast</a>
        <a href="#m7">7. Valuation Analysis</a>
        <a href="#m8">8. Technical Analysis</a>
        <a href="#m9">9. Monitor Signals</a>
        <a href="#m10">10. Risk Disclosure</a>
    </div>
</div>

<div class="max-w">

<!-- Tagline -->
<div class="highlight-box" style="margin-top:1.5rem;">
    <p class="body font-medium">{tagline or "Investment thesis tagline not available."}</p>
</div>
'''

    # Render each module
    module_renderers = [
        ('m1', '1. Investment Thesis (投资概要)', _render_module_1_investment_thesis, 'investment_thesis'),
        ('m2', '2. Investment Rationale & Risk (投资逻辑与风险)', _render_module_2_investment_rationale, 'investment_rationale'),
        ('m3', '3. Industry Analysis (行业分析)', _render_module_3_industry_analysis, 'industry_analysis'),
        ('m4', '4. Company Analysis (公司分析)', _render_module_4_company_analysis, 'company_analysis'),
        ('m5', '5. Financial Analysis (财务分析)', _render_module_5_financial_analysis, 'financial_analysis'),
        ('m6', '6. Earnings Forecast (盈利预测)', _render_module_6_earnings_forecast, 'earnings_forecast'),
        ('m7', '7. Valuation Analysis (估值分析)', _render_module_7_valuation_analysis, 'valuation_analysis'),
        ('m8', '8. Technical Analysis (技术面分析)', _render_module_8_technical_analysis, 'technical_analysis'),
        ('m9', '9. Key Monitor Signals (后续关注信号)', _render_module_9_monitor_signals, 'monitor_signals'),
        ('m10', '10. Risk Disclosure (风险提示)', _render_module_10_risk_disclosure, 'risk_disclosure'),
    ]

    for anchor, title, renderer, key in module_renderers:
        html += f'''
<!-- {title} -->
<section class="section page-break" id="{anchor}">
    <h2 class="section-title">{title}</h2>
    {renderer(outputs.get(key, {}))}
</section>
'''

    # Editor's overall assessment
    overall = editor.get('overall_assessment', '')
    if overall:
        html += f'''
<section class="section">
    <h2 class="section-title">Overall Assessment</h2>
    <div class="highlight-box"><p class="body font-medium">{overall}</p></div>
</section>
'''

    # Disclaimer
    disc = meta.get('disclaimer_text', 'This report is generated by SanSi AI for informational purposes only and does not constitute investment advice. Investors should make independent decisions based on their own risk tolerance. Past performance is not indicative of future results.')
    source = meta.get('research_source', 'SanSi AI Equity Research')
    data_src = meta.get('data_source_text', 'Company Filings, FMP API')
    gen_time = datetime.now().strftime('%Y-%m-%d %H:%M UTC')

    html += f'''
<!-- Disclaimer -->
<div class="disclaimer">
    <p style="margin-bottom:0.25rem;"><strong>Powered by SanSi AI</strong> | {source}</p>
    <p>{disc}</p>
    <p style="margin-top:0.5rem;">Data: {data_src} &middot; Generated: {gen_time}</p>
</div>

</div><!-- /max-w -->
</body>
</html>'''

    return html


def _get_rating_class(rating: str) -> str:
    r = str(rating).strip().lower()
    if r in ('buy', 'outperform', 'overweight', 'strong buy', '买入', '增持'):
        return 'badge-buy'
    elif r in ('sell', 'underperform', 'underweight', 'strong sell', '减持'):
        return 'badge-sell'
    return 'badge-hold'


# ================================================================
# Convenience: render from JSON file paths
# ================================================================

def render_from_json_dir(json_dir: str, report_meta: dict = None) -> str:
    """Load all agent JSONs from a directory and render the full report."""
    import os

    agent_outputs = {}
    module_names = [
        'investment_thesis', 'investment_rationale', 'industry_analysis',
        'company_analysis', 'financial_analysis', 'earnings_forecast',
        'valuation_analysis', 'technical_analysis', 'monitor_signals',
        'risk_disclosure', 'editor',
    ]
    for name in module_names:
        path = os.path.join(json_dir, f'{name}.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                agent_outputs[name] = json.load(f)
        else:
            agent_outputs[name] = {}

    return render_10module_html(agent_outputs, report_meta)
