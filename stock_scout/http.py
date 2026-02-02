from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_TIMEOUT = 15


@dataclass(frozen=True)
class HttpResult:
    ok: bool
    status: int
    text: Optional[str] = None
    data: Optional[Any] = None
    error: Optional[str] = None


def fetch_text(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> HttpResult:
    req = Request(url, headers=headers or {})
    try:
        with urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return HttpResult(ok=True, status=response.status, text=body)
    except HTTPError as exc:
        return HttpResult(ok=False, status=exc.code, error=str(exc))
    except URLError as exc:
        return HttpResult(ok=False, status=0, error=str(exc))


def fetch_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> HttpResult:
    result = fetch_text(url, headers=headers, timeout=timeout)
    if not result.ok or result.text is None:
        return result
    try:
        payload = json.loads(result.text)
    except json.JSONDecodeError as exc:
        return HttpResult(ok=False, status=result.status, error=str(exc))
    return HttpResult(ok=True, status=result.status, text=result.text, data=payload)
