# SanSi

AI 驱动的美股专业研究工具。输入股票代码，生成券商研报级别的深度分析报告。

## 快速开始

```bash
# 1. 配置 API Keys
cp .env.example .env
# 编辑 .env 填入你的 API Keys

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 Web 应用
python run_web_app.py
# 浏览器打开 http://127.0.0.1:8888
```

或使用部署脚本：

```bash
chmod +x deploy.sh
./deploy.sh start
```

## CLI 使用

```bash
cd src/core/src

# Step 1: 生成财务分析
python generate_financial_analysis.py \
  --company-ticker AAPL \
  --company-name "Apple Inc." \
  --generate-text-sections

# Step 2: 生成研究报告
python create_equity_report.py \
  --company-ticker AAPL \
  --company-name "Apple Inc." \
  --analysis-csv output/AAPL/analysis/financial_metrics_and_forecasts.csv
```

## 依赖服务

| 服务 | 用途 | 必需 |
|------|------|------|
| DeepSeek | LLM 文本生成 | 是 |
| FMP | 财务数据（主数据源） | 否，自动降级到 yfinance |
| yfinance | 财务数据（备用） | 否，自动安装 |

## 致谢

本项目衍生自 [AI4Finance Foundation](https://github.com/AI4Finance-Foundation) 的 [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot)。

主要变更：
- 移除多智能体框架（AutoGen），保留股票研究引擎
- LLM 切换为 DeepSeek
- 增加 yfinance 作为备用数据源
- 简化项目结构和部署

## 许可证

Apache 2.0 — 详见 [LICENSE](LICENSE)
