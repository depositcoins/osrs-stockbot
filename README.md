# 🧠 OSRS StockBot

Forecast Old School RuneScape item prices using time-series analysis, deep learning, and sentiment analysis.

## 📦 Features

- 📈 ARIMA & LSTM forecasting models
- 🧠 Reddit sentiment scoring with VADER
- 🗃️ Real-time data from RuneScape Wiki API
- 📊 Streamlit dashboard UI
- 📓 Jupyter EDA + modeling notebook

---

## 🛠️ Setup

```bash
git clone https://github.com/yourusername/osrs-stockbot.git
cd osrs-stockbot
pip install -r requirements.txt
```

> Replace Reddit API credentials in `utils/fetch_sentiment.py` before use.

---

## 🚀 Usage

### 1. Fetch price data
```bash
python utils/fetch_prices.py
```

### 2. Fetch Reddit sentiment
```bash
python utils/fetch_sentiment.py
```

### 3. Run models
```bash
python models/arima_model.py
python models/lstm_model.py
python models/regression_model.py
```

### 4. Launch the dashboard
```bash
streamlit run app/dashboard.py
```

---

## 📊 Dashboard Preview

- Historical & predicted prices
- Sentiment tables
- Visual forecasts from all models

---

## 🤖 Models

| Model     | Method        | Use Case            |
|-----------|---------------|---------------------|
| ARIMA     | Stats-based   | Short-term trends   |
| LSTM      | Deep learning | Long-term sequences |
| Regression | Linear        | Sentiment response  |

---

## 📘 Credits

- OSRS Wiki API: https://prices.runescape.wiki/
- Reddit: r/2007scape
- Built with: Python, Streamlit, TensorFlow, StatsModels

Enjoy your flips 💰
