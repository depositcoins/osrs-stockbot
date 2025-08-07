import requests
import pandas as pd
from datetime import datetime

def get_osrs_prices(item_id: int, timestep: str = "5m") -> pd.DataFrame:
    """
    Fetch price timeseries for a given OSRS item from the RuneScape Wiki API.

    Args:
        item_id (int): The ID of the OSRS item.
        timestep (str): The timestep of the data. Options: "5m", "1h", "6h".

    Returns:
        pd.DataFrame: DataFrame containing timestamp, avgHighPrice, avgLowPrice.
    """
    url = f"https://prices.runescape.wiki/api/v1/osrs/timeseries?timestep={timestep}&id={item_id}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception("Failed to fetch data from RuneScape Wiki API.")

    data = response.json()["data"]
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df = df[["timestamp", "avgHighPrice", "avgLowPrice"]]
    return df

if __name__ == "__main__":
    ITEM_ID = 30753  # Oathplate chest
    df = get_osrs_prices(ITEM_ID, "1h")
    df.to_csv("data/price_history/oathplate_prices.csv", index=False)
    print(df.tail())
