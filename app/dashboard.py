# --- path shim so we can import ../utils ---
import os, sys
_APP_DIR = os.path.dirname(__file__)
_REPO_ROOT = os.path.abspath(os.path.join(_APP_DIR, ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
# -------------------------------------------


import streamlit as st
import pandas as pd
from difflib import get_close_matches
from utils.wiki_api import get_mapping, get_latest, get_timeseries

st.set_page_config(page_title="OSRS StockBot – Live", layout="wide")
st.title("📊 OSRS StockBot — Live Prices & Forecasts")

st.markdown(
    "Type any OSRS item name to see its **live price** from the OSRS Wiki API "
    "and pull a quick **price history** chart. Use the side panel to tweak options."
)

with st.sidebar:
    st.header("Search")
    query = st.text_input("Item name", value="Oathplate chest")
    timestep = st.selectbox("Timeseries interval", ["5m", "1h", "6h"], index=1)
    show_latest_table = st.checkbox("Show full latest-price table (matches only)", value=False)

mapping_df = get_mapping()
names = mapping_df["name"].tolist()

matches = []
if query.strip():
    matches = get_close_matches(query, names, n=10, cutoff=0.4)

if not matches:
    st.info("No matches found. Try a different search term.")
    st.stop()

choice = st.selectbox("Select item", matches, index=0)
row = mapping_df[mapping_df["name"] == choice].iloc[0]
item_id = int(row["id"])

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("ℹ️ Item")
    st.write(f"**Name:** {row['name']}")
    st.write(f"**ID:** `{item_id}`")
    if 'examine' in row and isinstance(row['examine'], str):
        st.caption(row['examine'])

    st.subheader("💱 Live Price")
    latest = get_latest(ids=[item_id])
    data = latest.get(str(item_id), {})
    if data:
        high = data.get("high")
        low = data.get("low")
        st.metric("Instant Buy (high)", f"{high:,} gp" if high else "—")
        st.metric("Instant Sell (low)", f"{low:,} gp" if low else "—")
    else:
        st.warning("No live price returned for this item.")

with col2:
    st.subheader("📈 Price History")
    ts = get_timeseries(item_id, timestep=timestep)
    if not ts.empty:
        st.line_chart(ts.set_index("timestamp")[["avgHighPrice", "avgLowPrice"]])
    else:
        st.info("No timeseries data returned for this item/timestep.")

if show_latest_table:
    ids = mapping_df[mapping_df["name"].isin(matches)]["id"].astype(int).tolist()
    latest_many = get_latest(ids=ids)
    rows = []
    for i in ids:
        d = latest_many.get(str(i), {})
        rows.append({
            "id": i,
            "name": mapping_df.loc[mapping_df["id"] == i, "name"].values[0],
            "high": d.get("high"),
            "low": d.get("low"),
            "highTime": d.get("highTime"),
            "lowTime": d.get("lowTime"),
        })
    table = pd.DataFrame(rows)
    st.subheader("🔎 Matched Items — Live Snapshot")
    st.dataframe(table)
