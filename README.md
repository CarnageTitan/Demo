# Quant Trading Model

A quantitative stock screening model that fetches market data via free APIs and recommends stocks to buy based on **Value**, **Momentum**, **RSI**, and **Volume** factors.

## Features

- **No API key required** — Uses [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance) by default
- **Optional Alpha Vantage** — Set `ALPHA_VANTAGE_API_KEY` for supplementary data (free key at [alphavantage.co](https://www.alphavantage.co/support/#api-key))
- **Quant factors**: P/E, P/B, dividend yield, price momentum, RSI, volume trend
- **Composite score 0–100** — Higher = stronger buy signal

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Analyze built-in watchlist (35 large-cap stocks)
python run_model.py

# Analyze specific tickers
python run_model.py AAPL MSFT GOOGL NVDA

# Show top 15 recommendations
python run_model.py --top 15

# Filter by minimum score
python run_model.py --min-score 60

# Use 2 years of history
python run_model.py --period 2y
```

## Output

| Symbol | Score | Price   | P/E  | 1M %   | RSI | Signal    |
|--------|-------|---------|------|--------|-----|-----------|
| NVDA   | 72.3  | $450.00 | 45.2 | +12.5% | 58  | STRONG BUY |
| AAPL   | 65.1  | $175.00 | 28.1 | +3.2%  | 52  | BUY       |

- **STRONG BUY**: Score ≥ 70
- **BUY**: Score ≥ 60
- **HOLD**: Score ≥ 50
- **WEAK**: Score < 50

## APIs Used

| API              | Key Required | Limits                  |
|------------------|--------------|-------------------------|
| **yfinance**     | No           | Reasonable rate limits  |
| **Alpha Vantage**| Yes (free)   | 5/min, 25/day free tier |

**FactSet**: If you have FactSet access, you can add a `data_fetcher_factset.py` module that fetches from the FactSet API and plug it into the same scoring pipeline in `quant_model.py`.

## Project Structure

```
├── run_model.py      # Main entry point
├── requirements.txt
├── README.md
└── src/
    ├── data_fetcher.py   # Fetch from yfinance / Alpha Vantage
    └── quant_model.py    # Scoring logic (value, momentum, RSI, volume)
```

## Disclaimer

**For research and education only.** Not financial advice. Past performance does not guarantee future results. Always do your own due diligence before investing.
