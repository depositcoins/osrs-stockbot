import requests
import pandas as pd
from functools import lru_cache

WIKI_BASE = "https://prices.runescape.wiki/api/v1/osrs"

def _get_json(url: str):
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()

@lru_cache(maxsize=1)
def get_mapping() -> pd.DataFrame:
    data = _get_json(f"{WIKI_BASE}/mapping")
    df = pd.DataFrame(data)
    keep_cols = [c for c in ["id", "name", "examine", "members", "highalch"] if c in df.columns]
    return df[keep_cols].dropna(subset=["id", "name"]).reset_index(drop=True)

def get_latest(ids=None) -> dict:
    data = _get_json(f"{WIKI_BASE}/latest")
    prices = data.get("data", {})
    if ids is None:
        return prices
    ids_str = {str(i) for i in ids}
    return {k: v for k, v in prices.items() if k in ids_str}

def get_timeseries(item_id: int, timestep: str = "1h") -> pd.DataFrame:
    url = f"{WIKI_BASE}/timeseries?timestep={timestep}&id={item_id}"
    data = _get_json(url).get("data", [])
    if not data:
        return pd.DataFrame(columns=["timestamp", "avgHighPrice", "avgLowPrice"])
    df = pd.DataFrame(data)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    return df
