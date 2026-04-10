#!/usr/bin/env python3
"""
Quant Trading Model - Stock Buy Recommendations

Uses free APIs (yfinance primary, Alpha Vantage optional) to fetch data
and scores stocks on Value, Momentum, RSI, and Volume factors.

Usage:
  python run_model.py                    # Analyze default watchlist
  python run_model.py AAPL MSFT GOOGL    # Analyze specific tickers
  python run_model.py --top 15           # Show top 15 recommendations
"""

import argparse
import sys
from pathlib import Path

# Allow running from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data_fetcher import fetch_yfinance, fetch_stock_fundamentals
from src.quant_model import score_stock
from src.backtest import run_monthly_backtest

# Default watchlist: diversified large/mid caps across sectors
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
    "JPM", "V", "WMT", "JNJ", "PG", "UNH", "HD", "DIS", "NFLX", "AMD",
    "INTC", "CRM", "ADBE", "CSCO", "PEP", "KO", "COST", "XOM", "CVX",
    "ABBV", "MRK", "TMO", "ABT", "LLY", "PFE", "BAC", "GS", "MS",
]


def run_backtest_main(tickers: list, args) -> int:
    """Monthly rebalance simulation; not predictive of live results."""
    import pandas as pd

    period = args.period if args.period in ("2y", "3y", "5y", "max") else "5y"
    if args.period not in ("2y", "3y", "5y", "max"):
        print(f"Note: Backtest uses period=5y (you passed {args.period!r}).")

    bench = args.benchmark.upper()
    fetch_list = list(dict.fromkeys(tickers + [bench, "^VIX"]))

    print("=" * 60)
    print("  RETAIL QUANT — Monthly backtest (research only)")
    print("=" * 60)
    print(f"Universe: {len(tickers)} names | Benchmark: {bench} | yfinance period: {period}")
    print()

    raw = fetch_yfinance(fetch_list, period=period)
    if raw is None or raw.empty:
        print("ERROR: Could not fetch price data.")
        return 1

    def series_for(sym: str, col: str) -> pd.Series:
        if len(fetch_list) == 1:
            return raw[col] if col in raw.columns else pd.Series(dtype=float)
        if isinstance(raw.columns, pd.MultiIndex) and sym in raw.columns.get_level_values(0):
            sub = raw[sym]
            return sub[col] if col in sub.columns else pd.Series(dtype=float)
        return pd.Series(dtype=float)

    spy_s = series_for(bench, "Close")
    vix_s = series_for("^VIX", "Close")

    try:
        res = run_monthly_backtest(
            raw,
            tickers,
            spy_close=spy_s,
            vix_close=vix_s if not args.no_regime else None,
            use_regime=not args.no_regime,
        )
    except ValueError as e:
        print(f"ERROR: {e}")
        return 1

    s = res.summary
    print("Results (past data only; not financial advice):")
    print(f"  Strategy total return: {s['total_return_strategy']*100:.1f}%")
    print(f"  {bench} total return:     {s['total_return_spy']*100:.1f}%")
    print(f"  Strategy CAGR:         {s['cagr_strategy']*100:.1f}%")
    print(f"  {bench} CAGR:             {s['cagr_spy']*100:.1f}%")
    print(f"  Strategy ann. vol:     {s['vol_ann_strategy']*100:.1f}%")
    print(f"  Strategy Sharpe (raw): {s['sharpe_strategy']:.2f}")
    print(f"  Max drawdown (strat):  {s['max_drawdown_strategy']*100:.1f}%")
    print(f"  Max drawdown ({bench}):  {s['max_drawdown_spy']*100:.1f}%")
    print(f"  Monthly rebalances:    {s['n_rebalances']}")
    print()
    print("Disclaimer: For education/research. Past performance does not guarantee future results.")
    print("=" * 60)
    return 0


def get_prices_and_volumes(price_data, tickers: list, symbol: str):
    """Extract Close and Volume series for a ticker from yfinance download result."""
    import pandas as pd

    if price_data is None or price_data.empty:
        return None, None

    # Single ticker: flat columns
    if len(tickers) == 1:
        prices = price_data["Close"] if "Close" in price_data.columns else None
        volumes = price_data["Volume"] if "Volume" in price_data.columns else None
        return prices, volumes

    # Multiple tickers: MultiIndex (Ticker, OHLCV)
    if isinstance(price_data.columns, pd.MultiIndex):
        lev0 = price_data.columns.get_level_values(0)
        if symbol in lev0:
            try:
                sub = price_data[symbol]
                prices = sub["Close"] if "Close" in sub.columns else None
                volumes = sub["Volume"] if "Volume" in sub.columns else None
                return prices, volumes
            except (KeyError, TypeError):
                pass
    return None, None


def main():
    parser = argparse.ArgumentParser(description="Quant Trading Model - Stock Recommendations")
    parser.add_argument(
        "tickers",
        nargs="*",
        default=None,
        help="Stock symbols to analyze (default: built-in watchlist)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top recommendations to show (default: 10)",
    )
    parser.add_argument(
        "--min-score",
        type=float,
        default=0,
        help="Minimum score to include (0-100, default: 0)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="1y",
        help="History period for yfinance (default: 1y)",
    )
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run monthly rebalance backtest vs SPY (uses longer history; price-only scores)",
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        default="SPY",
        help="Benchmark ticker for backtest (default: SPY)",
    )
    parser.add_argument(
        "--no-regime",
        action="store_true",
        help="Disable VIX-based equity scaling in backtest",
    )
    parser.add_argument(
        "--portfolio",
        action="store_true",
        help="After screening, print suggested long-only weights (retail limits)",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=12,
        help="Max names in portfolio weights (default: 12)",
    )
    args = parser.parse_args()

    tickers = args.tickers if args.tickers else DEFAULT_WATCHLIST
    tickers = [t.upper() for t in tickers]

    if args.backtest:
        return run_backtest_main(tickers, args)

    print("=" * 60)
    print("  QUANT TRADING MODEL - Stock Buy Recommendations")
    print("=" * 60)
    print(f"\nFetching data for {len(tickers)} stocks (yfinance, no API key required)...")
    print()

    # Fetch price data
    price_data = fetch_yfinance(tickers, period=args.period)
    if price_data is None or price_data.empty:
        print("ERROR: Could not fetch price data. Check your connection and ticker symbols.")
        return 1

    # Fetch fundamentals
    fundamentals = fetch_stock_fundamentals(tickers)

    # Score each stock
    scores = []
    for symbol in tickers:
        prices, volumes = get_prices_and_volumes(price_data, tickers, symbol)
        fund = fundamentals.get(symbol, {})
        result = score_stock(symbol, prices, volumes, fund)
        scores.append(result)

    # Sort by total score descending
    scores.sort(key=lambda x: x["total_score"], reverse=True)

    # Filter by min score
    scores = [s for s in scores if s["total_score"] >= args.min_score]

    # Display
    print(f"{'Symbol':<8} {'Score':<7} {'Price':<10} {'P/E':<8} {'1M %':<8} {'RSI':<6} {'Signal'}")
    print("-" * 60)

    for s in scores[: args.top]:
        price_str = f"${s['price']:.2f}" if s["price"] else "N/A"
        pe_str = f"{s['pe_ratio']:.1f}" if s["pe_ratio"] else "N/A"
        mom_str = f"{s['momentum_1m_pct']:+.1f}%" if s["momentum_1m_pct"] is not None else "N/A"
        rsi_str = f"{s['rsi']:.0f}" if s["rsi"] is not None else "N/A"

        if s["total_score"] >= 70:
            signal = "STRONG BUY"
        elif s["total_score"] >= 60:
            signal = "BUY"
        elif s["total_score"] >= 50:
            signal = "HOLD"
        else:
            signal = "WEAK"

        print(f"{s['symbol']:<8} {s['total_score']:<7.1f} {price_str:<10} {pe_str:<8} {mom_str:<8} {rsi_str:<6} {signal}")

    print()
    print("Top picks to consider:")
    strong = [x["symbol"] for x in scores if x["total_score"] >= 65]
    if strong:
        print(f"  Strong candidates (score >= 65): {', '.join(strong[:5])}")

    if args.portfolio:
        from src.portfolio import build_long_only_weights, sector_exposure
        from src.regime import equity_multiplier, fetch_vix_close

        sc_map = {x["symbol"]: x["total_score"] for x in scores}
        sec_map = {
            sym: (fundamentals.get(sym) or {}).get("sector") or "Unknown"
            for sym in tickers
        }
        w = build_long_only_weights(
            sc_map,
            sectors=sec_map,
            top_n=args.top_n,
            max_position=0.12,
            max_sector=0.40,
            score_floor=45.0,
        )
        vx = fetch_vix_close()
        mult = equity_multiplier(vx)
        print()
        eq_deployed = sum(w.values())
        print("Suggested portfolio weights (long-only; per-name cap 12%, sector cap 40%):")
        if vx is not None:
            print(f"  VIX ~{vx:.1f} → scale listed % by {mult:.0%} (overlay cash = rest)")
        for sym in sorted(w, key=w.get, reverse=True):
            pct = w[sym] * mult * 100
            print(f"  {sym:<6} {pct:5.2f}%  (pre-overlay {w[sym]*100:.2f}%)")
        if w:
            strat_cash = (1.0 - eq_deployed * mult) * 100
            print(f"  Implied cash (strategy + overlay): {strat_cash:.1f}%")
        print("  Sector mix (pre-overlay weights):")
        for sec, ex in sector_exposure(w, sec_map).items():
            print(f"    {sec}: {ex*100:.1f}%")

    print()
    print("Disclaimer: This is for research/education only. Not financial advice.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
