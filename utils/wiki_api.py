# utils/wiki_api.py
import time
import requests
import pandas as pd
from functools import lru_cache

WIKI_BASE = "https://prices.runescape.wiki/api/v1/osrs"

# Be a good API citizen: identify the app
DEFAULT_HEADERS = {
    "User-Agent": "OSRS-StockBot/1.0 (+https://github.com/depositcoins/osrs-stockbot)"
}

def _get_json(url: str, retries: int = 4, backoff: float = 0.75):
    """
    GET JSON with retries & exponential backoff.
    Returns {} on failure so callers can handle gracefully.
    """
    attempt = 0
    while True:
        try:
            resp = requests.get(url, headers=DEFAULT_HEADERS, timeout=20)
            if resp.status_code == 200:
                return resp.json()
            # For 429/5xx, sleep then retry
            if resp.status_code in (429, 500, 502, 503, 504):
                attempt += 1
                if attempt > retries:
                    return {}
                time.sleep(backoff * (2 ** (attempt - 1)))
            else:
                # Non-retryable error
                return {}
        except requests.RequestException:
            attempt += 1
            if attempt > retries:
                return {}
            time.sleep(backoff * (2 ** (attempt - 1)))

@lru_cache(maxsize=1)
def get_mapping() -> pd.DataFrame:
    data = _get_json(f"{WIKI_BASE}/mapping")
    df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame([])
    if df.empty:
        return pd.DataFrame(columns=["id", "name"])
    keep_cols = [c for c in ["id", "name", "examine", "members", "highalch"] if c in df.columns]
    return df[keep_cols].dropna(subset=["id", "name"]).reset_index(drop=True)

def get_latest(ids=None) -> dict:
    js = _get_json(f"{WIKI_BASE}/latest")
    prices = js.get("data", {}) if isinstance(js, dict) else {}
    if ids is None:
        return prices
    ids_str = {str(i) for i in ids}
    return {k: v for k, v in prices.items() if k in ids_str}

def get_timeseries(item_id: int, timestep: str = "1h") -> pd.DataFrame:
    """
    Fetch price history. Returns empty DataFrame on failure (UI handles gracefully).
    timestep ∈ {"5m","1h","6h"}.
    """
    url = f"{WIKI_BASE}/timeseries?timestep={timestep}&id={item_id}"
    js = _get_json(url)
    data = js.get("data", []) if isinstance(js, dict) else []
    if not data:
        return pd.DataFrame(columns=["timestamp", "avgHighPrice", "avgLowPrice"])
    df = pd.DataFrame(data
