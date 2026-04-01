"""
Retail-oriented portfolio construction: long-only weights with position limits.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Optional


def _score_weights(symbols: list[str], scores: dict[str, float], score_floor: float) -> dict[str, float]:
    raw: dict[str, float] = {}
    for s in symbols:
        sc = scores.get(s, 0.0)
        if sc < score_floor:
            continue
        excess = max(sc - 50.0, 0.01)
        raw[s] = excess**2
    total = sum(raw.values())
    if total <= 0:
        return {}
    return {s: v / total for s, v in raw.items()}


def _enforce_stock_caps(w: dict[str, float], max_position: float, max_rounds: int = 500) -> dict[str, float]:
    """Renormalize, then iteratively cap and redistribute surplus to uncapped names."""
    w = {k: float(v) for k, v in w.items() if v > 0}
    if not w:
        return {}

    for _ in range(max_rounds):
        tot = sum(w.values())
        if tot <= 0:
            return {}
        w = {k: v / tot for k, v in w.items()}

        over = [k for k, v in w.items() if v > max_position + 1e-12]
        if not over:
            return w

        surplus = sum(w[k] - max_position for k in over)
        for k in over:
            w[k] = max_position

        under = [k for k, v in w.items() if v < max_position - 1e-12]
        if not under:
            return w

        s_u = sum(w[k] for k in under)
        if s_u <= 1e-15:
            eq = surplus / len(under)
            for k in under:
                w[k] = min(w[k] + eq, max_position)
            continue

        for k in under:
            w[k] += surplus * (w[k] / s_u)
            if w[k] > max_position:
                w[k] = max_position

    tot = sum(w.values())
    return {k: v / tot for k, v in w.items() if v > 0} if tot > 0 else {}


def _enforce_sector_caps(
    w: dict[str, float],
    sectors: dict[str, str],
    max_sector: float,
    max_rounds: int = 50,
) -> dict[str, float]:
    """
    Scale down any sector whose weight sum exceeds max_sector. Freed notional is
    implicit cash (no cross-sector redistribution), so constraints stay feasible.
    """
    w = {k: float(v) for k, v in w.items() if v > 0}
    for _ in range(max_rounds):
        by_sec: dict[str, list[str]] = defaultdict(list)
        for s in w:
            by_sec[sectors.get(s, "Unknown")].append(s)

        changed = False
        for _sec, syms in by_sec.items():
            sw = sum(w[s] for s in syms)
            if sw <= max_sector + 1e-12:
                continue
            factor = max_sector / sw
            for s in syms:
                w[s] *= factor
            changed = True

        if not changed:
            break

    return {k: v for k, v in w.items() if v > 1e-15}


def build_long_only_weights(
    scores: dict[str, float],
    sectors: Optional[dict[str, str]] = None,
    top_n: int = 12,
    max_position: float = 0.12,
    max_sector: float = 0.40,
    score_floor: float = 45.0,
) -> dict[str, float]:
    """
    Target weights per name (may sum to < 1 if caps bind — remainder is cash).
    """
    sectors = sectors or {}
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    picked = [s for s, sc in ranked if sc >= score_floor][:top_n]
    if not picked:
        return {}

    w = _score_weights(picked, scores, score_floor)
    if not w:
        eq = 1.0 / len(picked)
        w = {s: eq for s in picked}

    for _ in range(80):
        w0 = dict(w)
        w = _enforce_stock_caps(w, max_position)
        if sectors:
            w = _enforce_sector_caps(w, sectors, max_sector)
        if w == w0 or not w:
            break

    return w


def sector_exposure(weights: dict[str, float], sectors: dict[str, str]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for s, wt in weights.items():
        out[sectors.get(s, "Unknown")] += wt
    return dict(sorted(out.items(), key=lambda x: -x[1]))
