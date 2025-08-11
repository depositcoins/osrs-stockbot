import streamlit as st
import pandas as pd
from difflib import get_close_matches
from utils.wiki_api import get_mapping, get_latest, get_timeseries
from utils.indicators import add_indicators, compute_signals

st.set_page_config(page_title="OSRS StockBot – Live", layout="wide")

st.title("📊 OSRS StockBot — Live Prices & Forecasts")
st.markdown(
    "Search any OSRS item to see **live prices**, **history**, and **signals**. "
    "Use the **Watchlist** in the sidebar to pin items. "
    "**Tip:** Your current item & watchlist persist in the page URL for easy sharing."
)

# ---------- URL query params helpers ----------
def read_query_params():
    qp = st.query_params
    params = {'item': None, 'watch': []}
    if 'item' in qp and len(qp['item']) > 0:
        try:
            params['item'] = int(qp['item'][0])
        except Exception:
            pass
    if 'watch' in qp and len(qp['watch']) > 0:
        # comma-separated IDs
        try:
            params['watch'] = [int(x) for x in qp['watch'][0].split(',') if x.strip().isdigit()]
        except Exception:
            params['watch'] = []
    return params

def write_query_params(item_id=None, watch_ids=None):
    qp = {}
    if item_id is not None:
        qp['item'] = str(int(item_id))
    if watch_ids is not None and len(watch_ids) > 0:
        qp['watch'] = ','.join(str(int(x)) for x in watch_ids)
    st.query_params.update(qp)

# ---------- Session state ----------
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = {}

# Load mapping once
mapping_df = get_mapping()
names = mapping_df['name'].tolist()
id_to_name = dict(zip(mapping_df['id'], mapping_df['name']))

# Initialize from URL
params = read_query_params()
if params['watch']:
    for wid in params['watch']:
        if wid in id_to_name:
            st.session_state.watchlist[wid] = id_to_name[wid]

# ---------- Sidebar: search + watchlist ----------
with st.sidebar:
    st.header("Search")
    # Try to prefill from URL if present
    default_name = None
    if params['item'] and params['item'] in id_to_name:
        default_name = id_to_name[params['item']]
    query = st.text_input("Item name", value=(default_name or "Oathplate chest"))
    timestep = st.selectbox("Timeseries interval", ["5m", "1h", "6h"], index=1)

    matches = get_close_matches(query, names, n=10, cutoff=0.4) if query.strip() else []
    if not matches:
        st.info("No matches found.")
        st.stop()

    # If a URL item is present, prefer it in the selectbox when available
    default_index = 0
    if default_name and default_name in matches:
        default_index = matches.index(default_name)

    choice = st.selectbox("Select item", matches, index=default_index)
    row = mapping_df[mapping_df['name'] == choice].iloc[0]
    item_id = int(row['id'])

    # Write item to URL so it's shareable
    write_query_params(item_id=item_id, watch_ids=list(st.session_state.watchlist.keys()))

    st.markdown("---")
    st.subheader("Watchlist")
    st.caption("Add the selected item or manage existing entries. Saved only for this browser session, but IDs persist in URL.")

    if st.button("➕ Add selected item to watchlist"):
        st.session_state.watchlist[item_id] = row['name']
        write_query_params(item_id=item_id, watch_ids=list(st.session_state.watchlist.keys()))

    if st.session_state.watchlist:
        to_remove = st.multiselect("Remove items", options=[f"{i} — {n}" for i, n in st.session_state.watchlist.items()])
        if st.button("🗑 Remove selected"):
            ids = [int(opt.split(" — ")[0]) for opt in to_remove]
            for i in ids:
                st.session_state.watchlist.pop(i, None)
            write_query_params(item_id=item_id, watch_ids=list(st.session_state.watchlist.keys()))
    else:
        st.caption("Watchlist is empty.")

# ---------- Main: item panel ----------
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
    st.subheader("📈 Price History + Indicators")
    ts = pd.DataFrame()
    try:
        ts = get_timeseries(item_id, timestep=timestep)
    except Exception as e:
        st.warning("⚠ The Wiki API request failed (rate limit or network). Try again.")
        st.caption(str(e))

    if not ts.empty:
        # Add indicators
        feat = add_indicators(ts)
        st.line_chart(feat.set_index("timestamp")[["mid", "SMA7", "SMA30"]])

        # Signals table with color-coded actions
        sig = compute_signals(feat)
        if not sig.empty:
            # Color code: BUY green, SELL red, HOLD gray
            def _color_action(val):
                if val == "BUY":
                    return "background-color: #c6f6d5; font-weight: 700;"  # green-ish
                if val == "SELL":
                    return "background-color: #fed7d7; font-weight: 700;"  # red-ish
                return "background-color: #e2e8f0;"  # gray-ish
            st.subheader("🔎 Signals (SMA & RSI)")
            st.dataframe(sig.style.applymap(_color_action, subset=["Action"]), use_container_width=True)
    else:
        st.info("No timeseries data available for this item/interval right now.")

# ---------- Watchlist table ----------
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
