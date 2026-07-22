"""
Self-test for the 10+1 agent system using mock AAPL-like data.
Validates: Pydantic output structure, pipeline orchestration, prompt construction.
"""

import asyncio
import json
import os
import sys
import time

# Ensure we can import from the project
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from modules.equity_agents import (
    ModuleData,
    EquityResearchAgentManager,
    create_manager,
)


def build_mock_data() -> ModuleData:
    """Build realistic mock data for testing all agents."""

    # Financial metrics table (mimics the CSV output from financial_data_processor)
    financial_metrics = {
        "metrics": [
            "Revenue", "Revenue Growth", "Cost of Operations", "SG&A",
            "Contribution Profit", "Contribution Margin", "EBITDA", "EBITDA Margin",
            "SG&A Margin", "EPS", "PE Ratio", "Net Income", "Gross Profit",
            "Operating Income", "Free Cash Flow", "Total Assets",
            "Total Liabilities", "Total Equity", "ROE", "ROA",
            "Net Debt / EBITDA", "Current Ratio", "Debt / Equity",
        ],
        "2022A": [
            394328000000,    # Revenue
            "N/A",           # Revenue Growth (base year)
            223546000000,    # Cost of Operations
            25094000000,     # SG&A
            170782000000,    # Contribution Profit
            "43.3%",         # Contribution Margin
            130541000000,    # EBITDA
            "33.1%",         # EBITDA Margin
            "6.4%",          # SG&A Margin
            6.11,            # EPS
            24.8,            # PE Ratio
            99803000000,     # Net Income
            170782000000,    # Gross Profit
            119103000000,    # Operating Income
            111443000000,    # Free Cash Flow
            352755000000,    # Total Assets
            302083000000,    # Total Liabilities
            50672000000,     # Total Equity
            "196.9%",        # ROE
            "28.3%",         # ROA
            "1.1x",          # Net Debt / EBITDA
            "0.88",          # Current Ratio
            "5.96",          # Debt / Equity
        ],
        "2023A": [
            383285000000,
            "-2.8%",
            214137000000,
            24932000000,
            169148000000,
            "44.1%",
            123000000000,
            "32.1%",
            "6.5%",
            6.16,
            26.2,
            96995000000,
            169148000000,
            114301000000,
            99500000000,
            352583000000,
            290437000000,
            62146000000,
            "156.1%",
            "27.5%",
            "1.3x",
            "0.99",
            "4.67",
        ],
        "2024A": [
            391035000000,
            "+2.0%",
            210352000000,
            26027000000,
            180683000000,
            "46.2%",
            134500000000,
            "34.4%",
            "6.7%",
            6.52,
            30.1,
            102500000000,
            180683000000,
            126500000000,
            108000000000,
            364980000000,
            288000000000,
            76980000000,
            "150.0%",
            "28.1%",
            "1.2x",
            "0.95",
            "4.20",
        ],
        "2025E": [
            410586750000,    # Revenue (+5%)
            "+5.0%",
            218543000000,
            27331000000,
            192043750000,
            "46.8%",
            141000000000,
            "34.3%",
            "6.7%",
            6.98,
            28.6,
            108000000000,
            192043750000,
            133000000000,
            113000000000,
            None, None, None, None, None, None, None, None,
        ],
    }

    forecast_data = {
        "assumptions": {
            "revenue_growth": {"2025E": "5.0%", "2026E": "6.0%", "2027E": "5.5%"},
            "gross_margin": {"2025E": "46.8%", "2026E": "47.0%", "2027E": "47.2%"},
            "sga_ratio": {"2025E": "6.7%", "2026E": "6.6%", "2027E": "6.5%"},
            "capex_to_revenue": {"2025E": "3.0%", "2026E": "2.9%", "2027E": "2.8%"},
            "tax_rate": {"2025E": "16.0%", "2026E": "16.0%", "2027E": "16.0%"},
            "payout_ratio": {"2025E": "15%", "2026E": "15%", "2027E": "15%"},
        }
    }

    company_profile = {
        "companyName": "Apple Inc.",
        "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide. The company also offers related software, services, and accessories. Its products include iPhone, Mac, iPad, AirPods, Apple Watch, Apple TV, and HomePod. The company also provides AppleCare support, cloud services, and digital content through the App Store, Apple Music, Apple TV+, Apple Arcade, and Apple Fitness+. Apple serves consumers, small and mid-sized businesses, and education, enterprise, and government customers worldwide.",
        "ceo": "Timothy D. Cook",
        "ceoName": "Tim Cook",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "exchangeShortName": "NASDAQ",
        "fullTimeEmployees": 164000,
        "ipoDate": "1980-12-12",
        "website": "https://www.apple.com",
        "marketCap": 3500000000000,
        "revenue": 391035000000,
    }

    management = [
        {"name": "Tim Cook", "title": "CEO", "since": "2011", "background": "Joined Apple in 1998, previously COO. Former VP at Compaq and COO at Intelligent Electronics."},
        {"name": "Luca Maestri", "title": "CFO", "since": "2014", "background": "Former CFO at Xerox and Nokia Siemens Networks."},
        {"name": "Jeff Williams", "title": "COO", "since": "2015", "background": "Joined Apple in 1998, led iPhone operations and supply chain."},
    ]

    business_segments = [
        {"name": "iPhone", "revenue": 200000000000, "share": 0.51, "growth": -0.02, "key_driver": "iPhone upgrade cycle, emerging market penetration"},
        {"name": "Services", "revenue": 85000000000, "share": 0.22, "growth": 0.14, "key_driver": "App Store, Apple Music, iCloud subscriber growth"},
        {"name": "Mac", "revenue": 30000000000, "share": 0.08, "growth": 0.03, "key_driver": "M-series chip upgrade cycle"},
        {"name": "iPad", "revenue": 25000000000, "share": 0.06, "growth": -0.05, "key_driver": "Education and enterprise adoption"},
        {"name": "Wearables/Home/Accessories", "revenue": 40000000000, "share": 0.10, "growth": 0.02, "key_driver": "Apple Watch health features, AirPods refresh"},
    ]

    company_history = [
        {"year": "1976", "event": "Founded by Steve Jobs, Steve Wozniak, and Ronald Wayne"},
        {"year": "1980", "event": "IPO on NASDAQ at $22 per share"},
        {"year": "2007", "event": "iPhone launched, redefining the smartphone industry"},
        {"year": "2011", "event": "Tim Cook becomes CEO after Steve Jobs' passing"},
        {"year": "2015", "event": "Apple Watch launched, entering wearables market"},
        {"year": "2020", "event": "M1 chip announced, starting Mac transition from Intel"},
        {"year": "2024", "event": "Vision Pro launched, entering spatial computing"},
    ]

    industry_data = {
        "industry_name": "Consumer Electronics",
        "market_size": "$1.2 Trillion (global, 2024)",
        "historical_cagr": "+4.5% (2020-2024)",
        "forecast_cagr": "+5.5% (2025-2028)",
        "lifecycle_stage": "Mature, with premium segment showing above-average growth",
        "cr3": "~45%",
        "cr5": "~60%",
        "key_trends": [
            "AI integration into consumer devices accelerating",
            "Services ecosystem becoming primary profit driver",
            "Supply chain diversification away from China",
            "Premiumization trend benefiting established brands",
        ],
    }

    technical_indicators = {
        "sma50": "185.50",
        "sma200": "178.20",
        "rsi14": "52.3",
        "macd": "2.15",
        "macd_signal": "1.80",
        "macd_histogram": "0.35",
        "price": "190.00",
        "ma_signal": "Bullish",
        "rsi_signal": "Neutral",
        "macd_signal_label": "Bullish",
        "avg_volume_20d": "55000000",
        "latest_volume": "48000000",
        "volume_signal": "Normal",
        "overall_signal": "Bullish",
    }

    valuation_results = {
        "DCF": {
            "target_price": 205.00,
            "low_estimate": 175.00,
            "high_estimate": 235.00,
            "assumptions": {
                "wacc": "9.2%",
                "terminal_growth": "2.5%",
                "fcf_growth_1_5": "8.0%",
                "fcf_growth_6_10": "5.0%",
            },
        },
        "EV/EBITDA": {
            "target_price": 210.00,
            "low_estimate": 185.00,
            "high_estimate": 240.00,
            "target_multiple": "22.5x",
        },
        "Peer_Comparison": {
            "target_price": 195.00,
            "low_estimate": 170.00,
            "high_estimate": 220.00,
            "peers_used": ["MSFT", "GOOGL", "AMZN", "META"],
        },
        "Historical_Median": {
            "target_price": 198.00,
        },
    }

    peer_metrics = {
        "AAPL (Target)": {"revenue": "391B", "growth": "2.0%", "ebitda_margin": "34.4%", "pe": "30.1x", "market_cap": "3500B"},
        "MSFT": {"revenue": "245B", "growth": "15.2%", "ebitda_margin": "52.5%", "pe": "35.2x", "market_cap": "3200B"},
        "GOOGL": {"revenue": "328B", "growth": "9.8%", "ebitda_margin": "41.2%", "pe": "25.8x", "market_cap": "2100B"},
        "AMZN": {"revenue": "605B", "growth": "12.5%", "ebitda_margin": "18.5%", "pe": "42.1x", "market_cap": "2000B"},
        "META": {"revenue": "148B", "growth": "16.0%", "ebitda_margin": "50.8%", "pe": "28.5x", "market_cap": "1250B"},
    }

    catalyst_data = {
        "top_catalysts": [
            {"catalyst": "AI features in next iPhone cycle", "expected_date": "2025-09", "impact_level": "high", "sentiment": "positive"},
            {"catalyst": "Services revenue reaching $100B annual run rate", "expected_date": "2025-Q4", "impact_level": "medium", "sentiment": "positive"},
            {"catalyst": "Regulatory pressure from EU Digital Markets Act", "expected_date": "2025-H1", "impact_level": "high", "sentiment": "negative"},
        ]
    }

    risk_data = {
        "key_risks": [
            {"risk": "iPhone revenue concentration >50%", "severity": "high", "category": "operational"},
            {"risk": "China market dependence (~18% of revenue)", "severity": "high", "category": "operational"},
            {"risk": "Services growth deceleration if App Store regulation increases", "severity": "medium", "category": "industry"},
            {"risk": "Consumer electronics cyclicality", "severity": "medium", "category": "macro"},
            {"risk": "Current PE 30x leaves limited room for multiple expansion", "severity": "medium", "category": "valuation"},
        ]
    }

    news_data = [
        {"title": "Apple Reports Record Q4 Results, Services Revenue Hits All-Time High", "publishedDate": "2025-01-30", "text": "Apple announced record financial results with services revenue reaching an all-time high of $25 billion in the December quarter. The company highlighted strong iPhone 16 sales driven by AI features and growing adoption in emerging markets."},
        {"title": "Apple's AI Strategy: On-Device Intelligence Defines Next iPhone Era", "publishedDate": "2025-02-15", "text": "Apple is betting on on-device AI processing as its key differentiator. The A18 chip's neural engine enables real-time translation, advanced photo editing, and contextual Siri without sending data to the cloud, addressing privacy concerns."},
        {"title": "EU Regulators Fine Apple €500M Over App Store Practices", "publishedDate": "2025-03-01", "text": "The European Commission has fined Apple €500 million for anti-competitive practices related to App Store policies. Apple plans to appeal but may need to allow third-party app stores in the EU."},
    ]

    return ModuleData(
        company_name="Apple Inc.",
        company_ticker="AAPL",
        sector="Technology",
        industry="Consumer Electronics",
        current_price=190.00,
        market_cap=3500.0,
        financial_metrics=financial_metrics,
        forecast_data=forecast_data,
        company_profile=company_profile,
        management=management,
        business_segments=business_segments,
        company_history=company_history,
        industry_data=industry_data,
        technical_indicators=technical_indicators,
        valuation_results=valuation_results,
        peer_metrics=peer_metrics,
        catalyst_data=catalyst_data,
        risk_data=risk_data,
        news_data=news_data,
        language="en",
    )


async def test_single_agent(mgr: EquityResearchAgentManager, name: str, data: ModuleData):
    """Test a single agent and print result summary."""
    print(f"\n{'='*60}")
    print(f"  Agent: {name}")
    print(f"{'='*60}")
    t0 = time.time()
    try:
        result = await mgr.generate_module(name, data)
        elapsed = time.time() - t0

        if "error" in result:
            print(f"  FAILED ({elapsed:.1f}s): {result['error'][:200]}")
            return None
        else:
            # Print key fields
            keys = list(result.keys())
            print(f"  OK ({elapsed:.1f}s) — {len(keys)} top-level fields: {keys[:6]}...")
            # Show first field value (truncated)
            if keys:
                first_val = str(result[keys[0]])
                if len(first_val) > 300:
                    first_val = first_val[:300] + "..."
                print(f"  [{keys[0]}]: {first_val}")
            return result
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  EXCEPTION ({elapsed:.1f}s): {e}")
        return None


async def test_full_pipeline(mgr: EquityResearchAgentManager, data: ModuleData):
    """Run all 3 phases and validate results."""
    print(f"\n{'#'*60}")
    print(f"  FULL PIPELINE TEST")
    print(f"{'#'*60}")
    t0 = time.time()

    try:
        results = await mgr.generate_all(data)
        elapsed = time.time() - t0
        print(f"\n  Pipeline completed in {elapsed:.1f}s")
        print(f"  Modules generated: {len(results)}")

        # Validate each module
        expected = [
            "industry_analysis", "company_analysis", "financial_analysis",
            "earnings_forecast", "valuation_analysis", "technical_analysis",
            "investment_rationale", "risk_disclosure", "monitor_signals",
            "investment_thesis", "editor",
        ]
        passed = 0
        failed = 0
        for mod in expected:
            if mod in results:
                r = results[mod]
                if "error" in r:
                    print(f"  [{mod}] FAILED: {r['error'][:100]}")
                    failed += 1
                else:
                    key_count = len(r)
                    print(f"  [{mod}] OK — {key_count} fields")
                    passed += 1
            else:
                print(f"  [{mod}] MISSING")
                failed += 1

        print(f"\n  Results: {passed} passed, {failed} failed, {len(results)} total")
        return results
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  Pipeline EXCEPTION ({elapsed:.1f}s): {e}")
        import traceback
        traceback.print_exc()
        return {}


def main():
    print("=" * 60)
    print("  SanSi Agent System Self-Test")
    print("  Model: DeepSeek (deepseek-chat)")
    print("=" * 60)

    # Check API key
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        # Try loading .env
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env"))
        api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("\nERROR: DEEPSEEK_API_KEY not set. Cannot run live tests.")
        print("Set it in .env file or environment variable.")
        return

    os.environ["OPENAI_API_KEY"] = api_key
    os.environ.setdefault("DEEPSEEK_BASE_URL", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"))
    os.environ.setdefault("DEEPSEEK_MODEL", os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))

    model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    print(f"  Base URL: {base_url}")
    print(f"  Model: {model}")

    data = build_mock_data()
    mgr = create_manager(model=model)

    # Choose test mode
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="Run full pipeline test")
    ap.add_argument("--module", type=str, default=None, help="Test a single module (e.g. industry_analysis)")
    args = ap.parse_args()

    if args.module:
        asyncio.run(test_single_agent(mgr, args.module, data))
    elif args.full:
        asyncio.run(test_full_pipeline(mgr, data))
    else:
        # Default: test one Phase 1 module (fastest)
        print("\n  Quick mode: testing single module (industry_analysis)")
        print("  Use --full for full pipeline, --module X for specific module")
        asyncio.run(test_single_agent(mgr, "industry_analysis", data))

    print("\nDone.")


if __name__ == "__main__":
    main()
