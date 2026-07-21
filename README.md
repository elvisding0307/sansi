# SanSi - AI-Powered Equity Research Report Generator

Generate professional investment bank-style equity research reports with AI.

## Features

- **Financial data fetching** — income statement, balance sheet, cash flow (FMP + yfinance fallback)
- **3-year forecasts** — revenue, EBITDA, margin projections
- **AI report writing** — 8 sections written by LLM (DeepSeek by default)
- **Peer comparison** — EBITDA and EV/EBITDA peer analysis
- **Valuation** — DCF, DDM, LBO, comparable company analysis
- **Sensitivity & catalyst analysis** — risk assessment and event detection
- **Charts** — 10+ chart types (revenue, EBITDA, waterfall, radar, etc.)
- **HTML + PDF output** — professional investment bank-style reports
- **Web UI** — FastAPI dashboard with authentication

## Quick Start

### Prerequisites
- Python 3.10-3.11
- DeepSeek API key (or any OpenAI-compatible API)
- FMP API key (optional, falls back to yfinance)

### Setup

```bash
# 1. Configure API keys
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start web app
python run_web_app.py
# Open http://127.0.0.1:8888
```

Or use the deploy script:

```bash
chmod +x deploy.sh
./deploy.sh start
```

### CLI usage

```bash
cd src/core/src

# Step 1: Generate financial analysis
python generate_financial_analysis.py \
  --company-ticker AAPL \
  --company-name "Apple Inc." \
  --generate-text-sections

# Step 2: Create equity report
python create_equity_report.py \
  --company-ticker AAPL \
  --company-name "Apple Inc." \
  --analysis-csv output/AAPL/analysis/financial_metrics_and_forecasts.csv
```

## Architecture

```
User Input (ticker)
  → fetch financial data (FMP → yfinance fallback)
  → calculate metrics + forecasts (pure Python)
  → generate AI text sections (DeepSeek)
  → create charts (matplotlib/seaborn)
  → render HTML + PDF report
```

## API Services

| Service | Purpose | Required |
|---------|---------|----------|
| DeepSeek | LLM text generation | Yes |
| FMP | Financial data (primary) | No, falls back to yfinance |
| yfinance | Financial data (fallback) | No, auto-installed |
| Adanos | Retail sentiment (optional) | No |

## Acknowledgments

This project is derived from [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot), an open-source AI agent platform for financial analysis by the [AI4Finance Foundation](https://github.com/AI4Finance-Foundation).

Key changes from the original FinRobot:
- Removed the multi-agent framework (AutoGen), retained only the equity research engine
- Replaced OpenAI with DeepSeek for LLM inference
- Added yfinance as a fallback data source when FMP is unavailable
- Added full Chinese/English i18n support for UI and report generation
- Simplified project structure and deployment

## License

Apache 2.0 — see [LICENSE](LICENSE)
