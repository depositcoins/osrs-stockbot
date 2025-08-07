import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
import warnings

warnings.filterwarnings("ignore")

def load_price_data(csv_path="data/price_history/oathplate_prices.csv"):
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    df = df.resample("D").mean().dropna()  # Resample to daily average
    return df

def train_arima_model(df, column="avgHighPrice", order=(2, 1, 2)):
    model = ARIMA(df[column], order=order)
    model_fit = model.fit()
    return model_fit

def forecast_prices(model_fit, steps=7):
    forecast = model_fit.forecast(steps=steps)
    return forecast

if __name__ == "__main__":
    df = load_price_data()
    model = train_arima_model(df)
    prediction = forecast_prices(model, steps=7)

    # Plot results
    plt.figure(figsize=(10, 5))
    df["avgHighPrice"].plot(label="Historical Price")
    prediction.index = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=7)
    prediction.plot(label="Forecast", color="orange")
    plt.title("Oathplate Chest Price Forecast (7-day ARIMA)")
    plt.xlabel("Date")
    plt.ylabel("GP")
    plt.legend()
    plt.tight_layout()
    plt.savefig("data/price_history/arima_forecast.png")
    plt.show()
