import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler

def load_price_data(csv_path="data/price_history/oathplate_prices.csv"):
    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)
    df = df.resample("D").mean().dropna()
    return df

def prepare_data(df, column="avgHighPrice", window_size=14):
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[[column]])

    X, y = [], []
    for i in range(window_size, len(scaled)):
        X.append(scaled[i-window_size:i, 0])
        y.append(scaled[i, 0])

    X, y = np.array(X), np.array(y)
    X = X.reshape((X.shape[0], X.shape[1], 1))  # 3D input for LSTM
    return X, y, scaler

def build_lstm_model(input_shape):
    model = Sequential()
    model.add(LSTM(64, return_sequences=True, input_shape=input_shape))
    model.add(Dropout(0.2))
    model.add(LSTM(64))
    model.add(Dropout(0.2))
    model.add(Dense(1))
    model.compile(optimizer="adam", loss="mean_squared_error")
    return model

def plot_predictions(actual, predicted):
    plt.figure(figsize=(10, 5))
    plt.plot(actual, color='blue', label='Actual Price')
    plt.plot(predicted, color='orange', label='Predicted Price')
    plt.title('LSTM Forecast - Oathplate Chest')
    plt.xlabel('Time')
    plt.ylabel('Price (normalized)')
    plt.legend()
    plt.tight_layout()
    plt.savefig("data/price_history/lstm_forecast.png")
    plt.show()

if __name__ == "__main__":
    df = load_price_data()
    X, y, scaler = prepare_data(df)
    model = build_lstm_model((X.shape[1], 1))
    model.fit(X, y, epochs=30, batch_size=16, verbose=1)

    predicted = model.predict(X)
    plot_predictions(y, predicted.flatten())
