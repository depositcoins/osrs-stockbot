import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import os

st.set_page_config(page_title="OSRS StockBot", layout="wide")

st.title("📊 OSRS Item Price Forecast Dashboard")
st.markdown("Forecasting item prices in Old School RuneScape using ARIMA and LSTM models.")

# Load price data
csv_path = "data/price_history/oathplate_prices.csv"
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    st.subheader("📈 Historical Price Chart")
    st.line_chart(df.set_index("timestamp")[["avgHighPrice", "avgLowPrice"]])
else:
    st.warning("Price data not found. Please run fetch_prices.py first.")

# Load ARIMA forecast image
if os.path.exists("data/price_history/arima_forecast.png"):
    st.subheader("🔮 ARIMA Forecast (7 Days)")
    st.image(Image.open("data/price_history/arima_forecast.png"))
else:
    st.info("Run arima_model.py to generate forecast.")

# Load LSTM forecast image
if os.path.exists("data/price_history/lstm_forecast.png"):
    st.subheader("🤖 LSTM Forecast")
    st.image(Image.open("data/price_history/lstm_forecast.png"))
else:
    st.info("Run lstm_model.py to generate LSTM forecast.")

# Display sentiment data
sentiment_path = "data/sentiment/oathplate_sentiment.csv"
if os.path.exists(sentiment_path):
    st.subheader("🧠 Reddit Sentiment Overview")
    sentiment_df = pd.read_csv(sentiment_path)
    st.dataframe(sentiment_df[["title", "created", "sentiment_compound"]].sort_values("created", ascending=False).head(10))
else:
    st.warning("Sentiment data not found. Please run fetch_sentiment.py.")
