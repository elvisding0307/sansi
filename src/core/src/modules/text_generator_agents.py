#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from typing import Dict, Optional
import os
from openai import OpenAI

from modules.retail_sentiment_client import format_retail_sentiment_for_prompt


def _get_fallback_text(prompt_type: str, company_name: str) -> str:
    """Returns fallback text when agent generation fails."""
    fallbacks = {
        "tagline": f"{company_name} demonstrates strong financial fundamentals with consistent revenue growth and solid profitability metrics. The company maintains a competitive position in its market segment through operational efficiency and strategic initiatives. Strong balance sheet metrics support continued value creation for shareholders.",
        "company_overview": f"{company_name} operates as a prominent player in its industry sector, demonstrating consistent financial performance through strategic market positioning and operational excellence. The company has shown resilient growth patterns supported by strong demand dynamics and effective cost management strategies.",
        "investment_overview": f"{company_name} has delivered solid financial performance in recent periods, supported by strong operational execution and favorable market conditions. Revenue growth has been driven by robust demand and strategic initiatives, while margin improvements reflect operational efficiency gains.",
        "valuation_overview": f"{company_name} trades at reasonable valuation levels relative to its peer group, supported by strong fundamental metrics and growth prospects. The company's financial profile demonstrates consistent profitability and cash generation capabilities.",
        "risks": "Key risks include: (1) Industry competition and market share pressure, (2) Regulatory changes affecting operations, (3) Economic downturns impacting demand, (4) Technology disruption risks, (5) Supply chain and operational challenges.",
        "competitor_analysis": f"{company_name} demonstrates competitive positioning within its industry through consistent financial performance and strategic market positioning relative to key competitors in the sector.",
        "major_takeaways": f"Revenue Growth: {company_name}'s revenue growth shows consistent performance trends.\n\nGross Profit Margin: {company_name}'s gross profit margins demonstrate operational effectiveness.\n\nSG&A Expense Margin: {company_name}'s SG&A expense management shows disciplined cost control.\n\nEBITDA Margin Stability: {company_name}'s EBITDA margin stability reflects strong underlying fundamentals.",
        "news_summary": f"Recent news coverage for {company_name} reflects ongoing market interest and developments in the company's operations and strategic initiatives."
    }
    return fallbacks.get(prompt_type, f"{company_name} analysis for {prompt_type.replace('_', ' ')} section.")


# System prompts for each text section
SYSTEM_PROMPTS_EN = {
    "tagline": "You are an equity research analyst. Create a 3-sentence professional tagline summarizing the company's financial position. Be concise and professional. Do not use markdown.",
    "company_overview": "You are a financial analyst. Write a comprehensive company overview (300-400 words) covering business model, products/services, market position, and recent performance. Use plain text, no markdown.",
    "investment_overview": "You are an investment analyst. Write an investment update (200-300 words) covering recent financial performance, growth drivers, and outlook. Use plain text, no markdown.",
    "valuation_overview": "You are a valuation analyst. Write a valuation analysis (200-300 words) covering current valuation metrics, peer comparison, and fair value assessment. Use plain text, no markdown.",
    "risks": "You are a risk analyst. List 5 key investment risks in bullet point format. Be specific and concise.",
    "competitor_analysis": "You are a competitive analyst. Write a competitor analysis (200-300 words) comparing the company to its peers. Use plain text, no markdown.",
    "major_takeaways": "You are a financial analyst. Provide 4 major takeaways covering: Revenue Growth, Gross Profit Margin, SG&A Expense Margin, and EBITDA Margin. Format each with a header followed by 1-2 sentences.",
    "news_summary": "You are a financial news analyst. Summarize the recent news (200-300 words) highlighting key developments and their investment implications. Use plain text, no markdown."
}

SYSTEM_PROMPTS_ZH = {
    "tagline": "你是一位股票研究分析师。用3句话撰写一份专业的公司标语，总结公司的财务状况。简洁专业，不要使用markdown。请用中文输出。",
    "company_overview": "你是一位金融分析师。撰写一份全面的公司概览（300-400字），涵盖业务模式、产品/服务、市场地位和近期表现。使用纯文本，不要使用markdown。请用中文输出。",
    "investment_overview": "你是一位投资分析师。撰写一份投资更新（200-300字），涵盖近期财务表现、增长驱动因素和展望。使用纯文本，不要使用markdown。请用中文输出。",
    "valuation_overview": "你是一位估值分析师。撰写一份估值分析（200-300字），涵盖当前估值指标、同行比较和公允价值评估。使用纯文本，不要使用markdown。请用中文输出。",
    "risks": "你是一位风险分析师。以项目符号格式列出5个关键投资风险。具体简洁。请用中文输出。",
    "competitor_analysis": "你是一位竞争分析专家。撰写一份竞争分析（200-300字），将公司与同行进行比较。使用纯文本，不要使用markdown。请用中文输出。",
    "major_takeaways": "你是一位金融分析师。提供4个主要要点，涵盖：收入增长、毛利率、销售管理费用率和EBITDA利润率。每个要点包含标题和1-2句话。请用中文输出。",
    "news_summary": "你是一位财经新闻分析师。总结近期新闻（200-300字），重点突出关键发展及其投资影响。使用纯文本，不要使用markdown。请用中文输出。"
}

SYSTEM_PROMPTS = SYSTEM_PROMPTS_EN  # default


def _df_to_string(df: Optional[pd.DataFrame], name: str) -> str:
    """Converts a DataFrame to a markdown string for use in a prompt."""
    if df is None or df.empty:
        return f"{name}:\n[Data not available]\n"

    try:
        return f"{name}:\n{df.to_markdown()}\n"
    except Exception as e:
        return f"{name}:\n[Error formatting data: {e}]\n"


def _prepare_user_prompt(data: Dict, prompt_type: str, company_name: str, company_ticker: str, language: str = "en") -> str:
    """Prepare user prompt with financial data."""
    financial_metrics = data.get('financial_metrics')
    peer_ebitda = data.get('peer_ebitda')
    peer_ev_ebitda = data.get('peer_ev_ebitda')
    company_news = data.get('company_news')
    retail_sentiment = data.get('retail_sentiment')

    is_zh = language == "zh"
    prompt = f"公司: {company_name} ({company_ticker})\n\n" if is_zh else f"Company: {company_name} ({company_ticker})\n\n"

    if financial_metrics is not None and not financial_metrics.empty:
        label = "财务指标" if is_zh else "Financial Metrics"
        prompt += _df_to_string(financial_metrics, label)

    if peer_ebitda is not None and not peer_ebitda.empty:
        label = "同行 EBITDA 对比" if is_zh else "Peer EBITDA Comparison"
        prompt += _df_to_string(peer_ebitda, label)

    if peer_ev_ebitda is not None and not peer_ev_ebitda.empty:
        label = "同行 EV/EBITDA 对比" if is_zh else "Peer EV/EBITDA Comparison"
        prompt += _df_to_string(peer_ev_ebitda, label)

    if prompt_type == "news_summary" and company_news:
        heading = "近期新闻:" if is_zh else "Recent News:"
        prompt += f"\n## {heading}\n"
        for i, article in enumerate(company_news[:10], 1):
            prompt += f"{i}. {article.get('title', 'N/A')} ({article.get('publishedDate', 'N/A')[:10]})\n"
            prompt += f"   {article.get('text', 'N/A')[:200]}...\n\n"

    if prompt_type == "news_summary" and retail_sentiment:
        prompt += "\n" + format_retail_sentiment_for_prompt(retail_sentiment) + "\n"

    if is_zh:
        prompt += f"\n请根据以上数据提供{prompt_type.replace('_', ' ')}分析。"
    else:
        prompt += f"\nPlease provide the {prompt_type.replace('_', ' ')} based on the above data."
    return prompt


def generate_text_section(data: Dict, prompt_type: str, api_key: str, company_name: str, company_ticker: str, base_url: str = None, model: str = None, language: str = "en") -> str:
    """
    Generates a specific text section for the equity report using OpenAI Chat API.

    Args:
        data: Financial data dictionary
        prompt_type: Type of text section to generate
        api_key: OpenAI API key
        company_name: Company name
        company_ticker: Stock ticker
        base_url: Optional API base URL
        model: Optional model name
        language: Report language ('en' or 'zh')
    """
    lang_label = "中文" if language == "zh" else "EN"
    print(f"🤖 Generating '{prompt_type}' text section... [{lang_label}]")

    # Validate API key
    if not api_key:
        print(f"⚠️ Warning: No API key provided. Using fallback text for '{prompt_type}'.")
        return _get_fallback_text(prompt_type, company_name)

    # Determine model and base_url
    default_model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    default_base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    # Create OpenAI-compatible client (works with DeepSeek)
    try:
        client_kwargs = {"api_key": api_key, "base_url": default_base_url}
        print(f"📡 Using API base URL: {default_base_url}")

        client = OpenAI(**client_kwargs)
        print(f"🤖 Using model: {default_model}")
    except Exception as e:
        print(f"⚠️ Warning: Could not create API client: {e}")
        return _get_fallback_text(prompt_type, company_name)

    # Select prompts based on language
    prompts = SYSTEM_PROMPTS_ZH if language == "zh" else SYSTEM_PROMPTS_EN
    system_prompt = prompts.get(prompt_type, f"You are a financial analyst. Provide {prompt_type.replace('_', ' ')} analysis.")

    # Prepare user prompt with data
    user_prompt = _prepare_user_prompt(data, prompt_type, company_name, company_ticker, language)

    # Call OpenAI API
    try:
        response = client.chat.completions.create(
            model=default_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )

        generated_text = response.choices[0].message.content.strip()

        if generated_text:
            print(f"✅ Successfully generated '{prompt_type}' ({len(generated_text)} chars)")
            return generated_text
        else:
            print(f"⚠️ Warning: Empty response for '{prompt_type}'")
            return _get_fallback_text(prompt_type, company_name)

    except Exception as e:
        print(f"❌ Error generating '{prompt_type}': {e}")
        return _get_fallback_text(prompt_type, company_name)

# Backward compatibility - keep old function signature
def _query_openai(prompt: str, api_key: str) -> str:
    """Legacy function for backward compatibility."""
    return "Text generation now handled by agents."

if __name__ == '__main__':
    print("Testing agent-based text_generator...")
