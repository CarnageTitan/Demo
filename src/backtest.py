"""
Monthly rebalance backtest using price-only scores (no fundamental lookahead).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from src.portfolio import build_long_only_weights
from src.quant_model import score_stock_price_only
from src.regime import equity_multiplier


@dataclass
class BacktestResult:
    strategy_daily: pd.Series
    benchmark_daily: pd.Series
    rebalance_dates: list[pd.Timestamp]
    summary: dict


def _ensure_dt_index(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.index, pd.DatetimeIndex):
        df = df.copy()
        df.index = pd.to_datetime(df.index)
    return df.sort_index()


def _close_matrix(price_data: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    """Build DataFrame of close prices (columns = tickers)."""
    if len(tickers) == 1:
        s = tickers[0]
        if isinstance(price_data.columns, pd.MultiIndex):
            sub = price_data[s]
            return pd.DataFrame({s: sub["Close"]}).pipe(_ensure_dt_index)
        return pd.DataFrame({s: price_data["Close"]}).pipe(_ensure_dt_index)

    closes = {}
    for sym in tickers:
        if sym not in price_data.columns.get_level_values(0):
            continue
        sub = price_data[sym]
        if "Close" in sub.columns:
            closes[sym] = sub["Close"]
    if not closes:
        return pd.DataFrame()
    out = pd.DataFrame(closes)
    return _ensure_dt_index(out)


def _volume_matrix(price_data: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if len(tickers) == 1:
        s = tickers[0]
        if isinstance(price_data.columns, pd.MultiIndex):
            sub = price_data[s]
            return pd.DataFrame({s: sub["Volume"]}).pipe(_ensure_dt_index)
        return pd.DataFrame({s: price_data["Volume"]}).pipe(_ensure_dt_index)

    vols = {}
    for sym in tickers:
        if sym not in price_data.columns.get_level_values(0):
            continue
        sub = price_data[sym]
        if "Volume" in sub.columns:
            vols[sym] = sub["Volume"]
    if not vols:
        return pd.DataFrame()
    return _ensure_dt_index(pd.DataFrame(vols))


def _month_end_dates(idx: pd.DatetimeIndex) -> list[pd.Timestamp]:
    if len(idx) == 0:
        return []
    d = pd.to_datetime(idx)
    df = pd.DataFrame({"ts": d})
    df["period"] = df["ts"].dt.to_period("M")
    last = df.groupby("period", sort=True)["ts"].max()
    return [pd.Timestamp(x) for x in last.tolist()]


def run_monthly_backtest(
    price_data: pd.DataFrame,
    tickers: list[str],
    spy_close: pd.Series,
    vix_close: Optional[pd.Series] = None,
    top_n: int = 12,
    max_position: float = 0.12,
    max_sector: float = 0.40,
    score_floor: float = 45.0,
    use_regime: bool = True,
    min_history_days: int = 130,
) -> BacktestResult:
    closes = _close_matrix(price_data, tickers)
    vols = _volume_matrix(price_data, tickers)
    spy_close = spy_close.copy()
    spy_close.index = pd.to_datetime(spy_close.index)
    spy_close = spy_close.sort_index().dropna()

    if closes.empty or len(closes) < min_history_days:
        raise ValueError("Insufficient price history for backtest.")

    common = closes.index.intersection(spy_close.index)
    closes = closes.loc[common]
    vols = vols.reindex(closes.index).ffill()
    spy_close = spy_close.loc[common]

    if vix_close is not None:
        vix_close = vix_close.copy()
        vix_close.index = pd.to_datetime(vix_close.index)
        vix_close = vix_close.sort_index().reindex(closes.index).ffill()

    rebal_dates = [d for d in _month_end_dates(closes.index) if d in closes.index]
    rebal_dates = [d for d in rebal_dates if closes.index.get_loc(d) >= min_history_days]

    daily_ret = closes.pct_change()
    spy_dr = spy_close.pct_change()

    port_ret = pd.Series(index=closes.index, dtype=float)
    port_ret.iloc[0] = 0.0

    weights_by_day: dict[pd.Timestamp, dict[str, float]] = {}
    current_w: dict[str, float] = {}
    mult = 1.0
    valid_syms = [s for s in tickers if s in closes.columns]
    n_eq = len(valid_syms)
    burn_in_w = {s: 1.0 / n_eq for s in valid_syms} if n_eq else {}

    for i, date in enumerate(closes.index):
        if i == 0:
            pass
        elif current_w:
            r_eq = 0.0
            for sym, wt in current_w.items():
                if sym in daily_ret.columns:
                    r_eq += wt * mult * float(daily_ret[sym].iloc[i])
            port_ret.iloc[i] = r_eq
        elif burn_in_w:
            r_eq = 0.0
            for sym, wt in burn_in_w.items():
                if sym in daily_ret.columns:
                    r_eq += wt * float(daily_ret[sym].iloc[i])
            port_ret.iloc[i] = r_eq
        else:
            port_ret.iloc[i] = 0.0

        if date in rebal_dates:
            hist_close = closes.loc[:date]
            hist_vol = vols.loc[:date]
            scores = {}
            for sym in tickers:
                if sym not in hist_close.columns:
                    continue
                pc = hist_close[sym].dropna()
                vv = hist_vol[sym].dropna() if sym in hist_vol.columns else None
                if len(pc) < 21:
                    continue
                if vv is not None:
                    vv = vv.reindex(pc.index).dropna()
                r = score_stock_price_only(sym, pc, vv if vv is not None and len(vv) > 0 else None)
                scores[sym] = r["total_score"]

            sectors = {s: "Equity" for s in tickers}
            w = build_long_only_weights(
                scores,
                sectors=sectors,
                top_n=top_n,
                max_position=max_position,
                max_sector=max_sector,
                score_floor=score_floor,
            )
            if w:
                current_w = w
            if use_regime and vix_close is not None and date in vix_close.index:
                vx = float(vix_close.loc[date])
                mult = equity_multiplier(vx)
            else:
                mult = 1.0
            weights_by_day[date] = dict(current_w) if current_w else dict(burn_in_w)

    strat_equity = (1 + port_ret.fillna(0)).cumprod()
    bench_equity = (1 + spy_dr.fillna(0).reindex(closes.index).fillna(0)).cumprod()

    dr_s = port_ret.fillna(0)
    dr_b = spy_dr.fillna(0).reindex(closes.index).fillna(0)

    years = len(dr_s) / 252.0 if len(dr_s) > 0 else 1.0
    total_s = float(strat_equity.iloc[-1] - 1)
    total_b = float(bench_equity.iloc[-1] - 1)
    vol_s = float(dr_s.std() * np.sqrt(252)) if dr_s.std() == dr_s.std() else 0.0
    vol_b = float(dr_b.std() * np.sqrt(252)) if dr_b.std() == dr_b.std() else 0.0
    sharpe_s = float((dr_s.mean() * 252) / (dr_s.std() * np.sqrt(252))) if dr_s.std() > 1e-12 else 0.0
    sharpe_b = float((dr_b.mean() * 252) / (dr_b.std() * np.sqrt(252))) if dr_b.std() > 1e-12 else 0.0

    dd_s = float((strat_equity / strat_equity.cummax() - 1).min())
    dd_b = float((bench_equity / bench_equity.cummax() - 1).min())

    summary = {
        "total_return_strategy": total_s,
        "total_return_spy": total_b,
        "cagr_strategy": float(strat_equity.iloc[-1] ** (1 / years) - 1) if years > 0 else 0.0,
        "cagr_spy": float(bench_equity.iloc[-1] ** (1 / years) - 1) if years > 0 else 0.0,
        "vol_ann_strategy": vol_s,
        "vol_ann_spy": vol_b,
        "sharpe_strategy": sharpe_s,
        "sharpe_spy": sharpe_b,
        "max_drawdown_strategy": dd_s,
        "max_drawdown_spy": dd_b,
        "n_rebalances": len(rebal_dates),
    }

    return BacktestResult(
        strategy_daily=strat_equity,
        benchmark_daily=bench_equity,
        rebalance_dates=rebal_dates,
        summary=summary,
    )
