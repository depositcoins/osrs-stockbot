"""Utility helpers for interacting with the Old School RuneScape Wiki price API.

The real project will eventually wrap these helpers in higher level services, but
for now we provide a small synchronous wrapper around the wiki endpoints with
polite client side rate limiting and a custom user agent.  The functions in this
module intentionally avoid raising exceptions so callers can decide how to handle
failures gracefully.

The functions implemented here are a subset of the behaviour described in the
project specification.  They are designed to be small, easy to test and
dependency free so they can be reused by both the backend API and the Discord
bot.
"""

from __future__ import annotations

import os
import threading
import time
from functools import lru_cache
from typing import Dict, Iterable, List, Optional

from urllib import request, error

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WIKI_BASE = "https://prices.runescape.wiki/api/v1/osrs"


def _user_agent() -> str:
    """Return the User‑Agent string for outbound requests.

    A default value is used when ``USER_AGENT`` is not defined.  The value is
    read at call time rather than module import so tests can override the
    environment variable with ``monkeypatch`` and reload this module.
    """

    return os.environ.get(
        "USER_AGENT",
        "OSRS-Merch-Bot/1.3 (contact: you@example.com)",
    )


# Maximum number of requests per second.  The API specification suggests at most
# four requests per second across all endpoints.
_MAX_RPS = 4
_MIN_INTERVAL = 1 / _MAX_RPS
_rate_lock = threading.Lock()
_last_request = 0.0


def _respect_rate_limit() -> None:
    """Sleep if necessary to maintain the global request rate limit."""

    global _last_request
    with _rate_lock:
        now = time.time()
        wait = _MIN_INTERVAL - (now - _last_request)
        if wait > 0:
            time.sleep(wait)
            now = time.time()
        _last_request = now


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------


def _get_json(url: str, retries: int = 4, backoff: float = 0.75) -> Dict:
    """GET ``url`` returning parsed JSON.

    The function retries on common transient errors with exponential backoff and
    honours the global request rate limit.  On any failure an empty ``dict`` is
    returned so callers can handle the absence of data as they see fit.
    """

    attempt = 0
    while True:
        _respect_rate_limit()
        try:
            req = request.Request(url, headers={"User-Agent": _user_agent()})
            with request.urlopen(req, timeout=20) as resp:
                status = resp.getcode()
                if status == 200:
                    import json

                    return json.load(resp)
                if status in {429, 500, 502, 503, 504}:
                    attempt += 1
                    if attempt > retries:
                        return {}
                    time.sleep(backoff * (2 ** (attempt - 1)))
                    continue
                return {}
        except (error.HTTPError, error.URLError, TimeoutError, ValueError):
            attempt += 1
            if attempt > retries:
                return {}
            time.sleep(backoff * (2 ** (attempt - 1)))


# ---------------------------------------------------------------------------
# Public API wrappers
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_mapping() -> List[Dict]:
    """Return the item mapping table as a list of dictionaries."""

    data = _get_json(f"{WIKI_BASE}/mapping")
    if not isinstance(data, list):
        return []

    allowed = {"id", "name", "examine", "members", "highalch"}
    out = []
    for row in data:
        if not isinstance(row, dict) or "id" not in row or "name" not in row:
            continue
        out.append({k: row.get(k) for k in allowed if k in row})
    return out


def get_latest(ids: Optional[Iterable[int]] = None) -> Dict[str, Dict]:
    """Fetch the latest price snapshot.

    ``ids`` may be an iterable of integers.  When provided the returned mapping
    is filtered to only those item ids.
    """

    js = _get_json(f"{WIKI_BASE}/latest")
    prices = js.get("data", {}) if isinstance(js, dict) else {}
    if ids is None:
        return prices

    ids_str = {str(i) for i in ids}
    return {k: v for k, v in prices.items() if k in ids_str}


_ALLOWED_TIMESTEPS = {"5m", "1h", "6h", "24h"}


def get_timeseries(item_id: int, timestep: str = "1h") -> List[Dict]:
    """Return historic prices for ``item_id`` as a list of dictionaries.

    Each dictionary contains ``timestamp`` (as a ``datetime`` object),
    ``avgHighPrice`` and ``avgLowPrice``.  If anything goes wrong an empty list
    is returned.
    """

    if timestep not in _ALLOWED_TIMESTEPS:
        raise ValueError(f"timestep must be one of {_ALLOWED_TIMESTEPS}")

    url = f"{WIKI_BASE}/timeseries?timestep={timestep}&id={item_id}"
    js = _get_json(url)
    data = js.get("data", []) if isinstance(js, dict) else []
    if not data:
        return []

    out: List[Dict] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        ts = row.get("timestamp")
        if ts is None:
            continue
        out.append(
            {
                "timestamp": time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.gmtime(int(ts))
                ),
                "avgHighPrice": row.get("avgHighPrice"),
                "avgLowPrice": row.get("avgLowPrice"),
            }
        )
    return out


__all__ = ["get_mapping", "get_latest", "get_timeseries"]

