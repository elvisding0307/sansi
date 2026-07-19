# FinRobot - AI-Powered Equity Research Report Generator

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
cp finrobot_equity/core/config/config.ini.example finrobot_equity/core/config/config.ini
# Edit config.ini with your keys

# 2. Set environment variables
export DEEPSEEK_API_KEY="your-key"
export DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
export DEEPSEEK_MODEL="deepseek-chat"

# 3. Install dependencies
pip install -r requirements-equity.txt

# 4. Start web app
python run_web_app.py
# Open http://127.0.0.1:8001
```

Or use the deploy script:

```bash
chmod +x deploy.sh
./deploy.sh start
```

### CLI usage

```bash
cd finrobot_equity/core/src

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

## License

Apache 2.0 — see [LICENSE](LICENSE)
