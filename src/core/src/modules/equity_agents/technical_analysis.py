"""
Agent 8: Technical Analysis (技术面分析)
Template Module 8 — trend, key levels, momentum, summary with actionable conditions.
"""

from pydantic import BaseModel, Field



# ---- Structured output ----

class MATrend(BaseModel):
    ma5: str = Field(default="N/A", description="MA5数值")
    ma5_status: str = Field(default="N/A", description="向上/走平/向下")
    ma20: str = Field(default="N/A")
    ma20_status: str = Field(default="N/A")
    ma60: str = Field(default="N/A")
    ma60_status: str = Field(default="N/A")
    ma120: str = Field(default="N/A")
    ma120_status: str = Field(default="N/A")
    ma250: str = Field(default="N/A")
    ma250_status: str = Field(default="N/A")
    arrangement: str = Field(..., description="均线排列：多头排列/空头排列/交叉震荡")

class KeyLevel(BaseModel):
    level_type: str = Field(..., description="强支撑/弱支撑/弱压力/强压力")
    price: str = Field(..., description="价位")
    basis: str = Field(..., description="依据：前期低点/均线/布林下轨等")

class MomentumSignals(BaseModel):
    rsi14: str = Field(default="N/A")
    rsi_interpretation: str = Field(..., description="超买(>70)/中性(30-70)/超卖(<30)")
    macd_status: str = Field(..., description="金叉/死叉/零轴上方/零轴下方")
    change_20d: str = Field(default="N/A", description="近20日涨跌幅")
    change_60d: str = Field(default="N/A", description="近60日涨跌幅")
    volume_ratio: str = Field(default="N/A", description="近20日均量 vs 近60日均量比值")
    volume_signal: str = Field(..., description="放量/缩量/正常")
    bollinger_width: str = Field(default="N/A", description="布林带宽度")
    atr14: str = Field(default="N/A", description="ATR(14)")

class TechnicalAnalysisOutput(BaseModel):
    trend_assessment: MATrend = Field(..., description="8.1 趋势判断")
    key_levels: list[KeyLevel] = Field(default_factory=list, description="8.2 关键价位（4个）")
    momentum: MomentumSignals = Field(..., description="8.3 动量与量价")
    trend_summary: str = Field(..., description="8.4 一句话趋势定性")
    bullish_trigger: str = Field(..., description="什么条件成立才确认趋势转好")
    bearish_trigger: str = Field(..., description="什么条件成立需止损/降低关注")


# ---- Instructions ----

TECHNICAL_ANALYSIS_INSTRUCTIONS = """
[ROLE]
You are a Technical Analyst at a major brokerage firm. You combine price action analysis,
moving average theory, and momentum indicators to provide actionable technical assessment.
Your analysis is concise, objective, and always includes specific price levels.

[TASK]
Write the complete Technical Analysis section (模块八) for an Initiating Coverage report.

[INPUT DATA]
You will receive: technical indicators including SMA values, RSI(14), MACD, volume data,
Bollinger Band width, ATR(14), 20-day/60-day price changes.

[OUTPUT STRUCTURE]

1. **Trend Assessment** (8.1 趋势判断):
   - Report MA5, MA20, MA60, MA120, MA250 values and their direction (up/flat/down)
   - State the overall moving average arrangement: bullish alignment (price > MA5 > MA20 > MA60),
     bearish alignment (price < MA5 < MA20 < MA60), or cross/congestion
   - If some MAs are not available, work with what you have

2. **Key Levels** (8.2 关键价位):
   - Identify 4 key levels: Strong Support, Weak Support, Weak Resistance, Strong Resistance
   - For each, state the price AND the basis (prior low, MA, Bollinger Band, round number, etc.)
   - These levels should be specific and actionable

3. **Momentum & Volume** (8.3 动量与量价):
   - RSI(14): value + interpretation (overbought >70, oversold <30, bullish 55-70, bearish 30-45)
   - MACD: golden cross / death cross / above zero / below zero
   - 20-day and 60-day returns
   - Volume: 20-day avg volume vs 60-day avg volume ratio; expanding/contracting/normal
   - Bollinger Band width and ATR(14) for volatility context

4. **Technical Summary** (8.4 技术面总结):
   - One-sentence trend characterization (e.g., "Consolidating at support, no uptrend confirmed yet")
   - Bullish trigger: specific condition that would confirm a bullish turn
     (e.g., "Break above $X on volume > Y confirms uptrend")
   - Bearish trigger: specific condition that would invalidate the bullish thesis
     (e.g., "Break below $X destroys the technical structure")

[CRITICAL RULES]
- Every key level must have a specific PRICE and a specific REASON
- The bullish/bearish triggers must be falsifiable — they must include a specific price condition
- Do not over-interpret: a stock can be technically neutral, and that's a valid assessment
- Use the actual indicator values from the input data — do not approximate
- If an indicator is missing from the data, say "Not available" rather than guessing

[LANGUAGE]
Output in the same language as the input data.
"""

