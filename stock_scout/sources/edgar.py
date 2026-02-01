from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any, Dict, Optional

from ..http import fetch_json


SEC_TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"

SEC_USER_AGENT = os.getenv(
    "SEC_USER_AGENT", "StockScout/1.0 (contact: dev@localhost)"
)

_TICKER_MAP: Optional[Dict[str, str]] = None


@dataclass(frozen=True)
class EdgarSummary:
    cik: Optional[str]
    revenue_growth_1y: Optional[float]
    latest_10k: Optional[str]
    latest_10q: Optional[str]
    days_since_10k: Optional[int]
    days_since_10q: Optional[int]


def _sec_headers() -> Dict[str, str]:
    return {"User-Agent": SEC_USER_AGENT}


def _parse_date(value: Optional[str]) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _days_since(value: Optional[str]) -> Optional[int]:
    parsed = _parse_date(value)
    if not parsed:
        return None
    today = datetime.now(timezone.utc).date()
    return (today - parsed).days


def _load_ticker_map() -> Dict[str, str]:
    global _TICKER_MAP
    if _TICKER_MAP is not None:
        return _TICKER_MAP
    result = fetch_json(SEC_TICKER_MAP_URL, headers=_sec_headers())
    mapping: Dict[str, str] = {}
    if result.ok and isinstance(result.data, dict):
        for item in result.data.values():
            ticker = str(item.get("ticker", "")).upper().strip()
            cik = str(item.get("cik_str", "")).strip()
            if ticker and cik:
                mapping[ticker] = cik.zfill(10)
    _TICKER_MAP = mapping
    return mapping


def cik_for_ticker(ticker: str) -> Optional[str]:
    return _load_ticker_map().get(ticker.upper().strip())


def _extract_revenue_growth_1y(facts: Dict[str, Any]) -> Optional[float]:
    candidates = [
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueGoodsNet",
    ]
    us_gaap = facts.get("facts", {}).get("us-gaap", {})
    for key in candidates:
        entry = us_gaap.get(key)
        if not entry:
            continue
        units = entry.get("units", {}).get("USD", [])
        annual = [
            item
            for item in units
            if item.get("fp") == "FY"
            and str(item.get("form", "")).startswith("10-K")
            and item.get("val") is not None
            and item.get("end")
        ]
        if len(annual) < 2:
            continue
        annual.sort(key=lambda x: x.get("end"))
        latest = annual[-1]
        prev = annual[-2]
        try:
            latest_val = float(latest["val"])
            prev_val = float(prev["val"])
        except (TypeError, ValueError):
            continue
        if prev_val <= 0:
            continue
        growth = ((latest_val - prev_val) / prev_val) * 100
        return round(growth, 2)
    return None


def _latest_filing_date(submissions: Dict[str, Any], form_name: str) -> Optional[str]:
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    for form, filing_date in zip(forms, dates):
        if str(form).upper() == form_name:
            return filing_date
    return None


def fetch_edgar_summary(ticker: str) -> EdgarSummary:
    cik = cik_for_ticker(ticker)
    if not cik:
        return EdgarSummary(
            cik=None,
            revenue_growth_1y=None,
            latest_10k=None,
            latest_10q=None,
            days_since_10k=None,
            days_since_10q=None,
        )
    facts_result = fetch_json(SEC_COMPANY_FACTS_URL.format(cik=cik), headers=_sec_headers())
    sub_result = fetch_json(SEC_SUBMISSIONS_URL.format(cik=cik), headers=_sec_headers())
    revenue_growth = None
    if facts_result.ok and isinstance(facts_result.data, dict):
        revenue_growth = _extract_revenue_growth_1y(facts_result.data)
    latest_10k = None
    latest_10q = None
    if sub_result.ok and isinstance(sub_result.data, dict):
        latest_10k = _latest_filing_date(sub_result.data, "10-K")
        latest_10q = _latest_filing_date(sub_result.data, "10-Q")
    return EdgarSummary(
        cik=cik,
        revenue_growth_1y=revenue_growth,
        latest_10k=latest_10k,
        latest_10q=latest_10q,
        days_since_10k=_days_since(latest_10k),
        days_since_10q=_days_since(latest_10q),
    )
