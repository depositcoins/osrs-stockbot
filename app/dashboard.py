import streamlit as st
import pandas as pd
from difflib import get_close_matches
from utils.wiki_api import get_mapping, get_latest, get_timeseries

st.set_page_config(page_title="OSRS StockBot – Live", layout="wide")

st.title("📊 OSRS StockBot — Live Prices & Forecasts")
st.markdown(
    "Type any OSRS item name to see its **live price** from the OSRS Wiki API, "
    "pull a **price history** chart, and manage a **Watchlist** that shows live snapshots."
)

# Session state watchlist
if "watchlist" not in st.session_state:
    st.session_state.watchlist = {}

def add_to_watchlist(item_id: int, name: str):
    st.session_state.watchlist[int(item_id)] = name

def remove_from_watchlist(ids):
    for i in ids:
        st.session_state.watchlist.pop(int(i), None)

# Sidebar
with st.sidebar:
    st.header("Search")
    mapping_df = get_mapping()
    names = mapping_df["name"].tolist()
    query = st.text_input("Item name", value="Oathplate chest")
    timestep = st.selectbox("Timeseries interval", ["5m", "1h", "6h"], index=1)
    matches = get_close_matches(query, names, n=10, cutoff=0.4) if query.strip() else []
    if not matches:
        st.info("No matches found.")
        st.stop()
    choice = st.selectbox("Select item", matches, index=0)
    row = mapping_df[mapping_df["name"] == choice].iloc[0]
    item_id = int(row["id"])

    st.markdown("---")
    st.subheader("Watchlist")
    st.caption("Add the selected item or manage existing entries. Saved only for this browser session.")
    if st.button("➕ Add selected item to watchlist"):
        add_to_watchlist(item_id, row["name"])

    if st.session_state.watchlist:
        to_remove = st.multiselect("Remove items", options=[f"{i} — {n}" for i, n in st.session_state.watchlist.items()])
        if st.button("🗑 Remove selected"):
            ids = [int(opt.split(" — ")[0]) for opt in to_remove]
            remove_from_watchlist(ids)
    else:
        st.caption("Watchlist is empty.")

# Main: item panel
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
    ts = pd.DataFrame()
    try:
        ts = get_timeseries(item_id, timestep=timestep)
    except Exception as e:
        st.warning("⚠ The Wiki API request failed (rate limit or network). Try again.")
        st.caption(str(e))

    if not ts.empty:
        st.line_chart(ts.set_index("timestamp")[["avgHighPrice", "avgLowPrice"]])
    else:
        st.info("No timeseries data available for this item/interval right now.")

# Watchlist table
st.markdown("---")
st.header("👀 Watchlist — Live Snapshot")
if st.session_state.watchlist:
    ids = list(st.session_state.watchlist.keys())
    latest_many = get_latest(ids=ids)
    rows = []
    for i in ids:
        d = latest_many.get(str(i), {})
        rows.append({
            "id": i,
            "name": st.session_state.watchlist[i],
            "high": d.get("high"),
            "low": d.get("low"),
            "highTime": d.get("highTime"),
            "lowTime": d.get("lowTime"),
        })
    table = pd.DataFrame(rows)
    st.dataframe(table, use_container_width=True)
else:
    st.caption("Add items to the watchlist from the sidebar to see them here.")
