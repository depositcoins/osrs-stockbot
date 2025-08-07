import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

def load_data(price_path="data/price_history/oathplate_prices.csv",
              sentiment_path="data/sentiment/oathplate_sentiment.csv"):
    prices = pd.read_csv(price_path, parse_dates=["timestamp"])
    sentiment = pd.read_csv(sentiment_path, parse_dates=["created"])

    # Resample prices daily
    prices = prices.set_index("timestamp").resample("D").mean().dropna()

    # Aggregate sentiment daily
    sentiment["created"] = sentiment["created"].dt.floor("D")
    sentiment_grouped = sentiment.groupby("created")["sentiment_compound"].mean()
    sentiment_grouped = sentiment_grouped.reindex(prices.index, method="ffill")

    df = prices.copy()
    df["sentiment"] = sentiment_grouped
    df.dropna(inplace=True)
    return df

def train_regression(df):
    X = df[["sentiment"]]
    y = df["avgHighPrice"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, shuffle=False, test_size=0.2)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    # Evaluation
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Plot
    plt.figure(figsize=(10, 5))
    plt.plot(y_test.index, y_test.values, label="Actual")
    plt.plot(y_test.index, y_pred, label="Predicted", linestyle="--")
    plt.title("Linear Regression: Price vs Sentiment")
    plt.xlabel("Time")
    plt.ylabel("Price (GP)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("data/price_history/regression_forecast.png")
    plt.show()

    print(f"R² Score: {r2:.3f}, MSE: {mse:.2f}")

if __name__ == "__main__":
    df = load_data()
    train_regression(df)
