import pandas as pd
import numpy as np

def add_indicators(ts: pd.DataFrame, price_col_high='avgHighPrice', price_col_low='avgLowPrice'):
    """Add SMA(7), SMA(30), and RSI(14) based on the average of high/low."""
    if ts.empty:
        return ts.copy()

    df = ts.copy()
    # Use a mid price for indicators
    if price_col_high in df and price_col_low in df:
        df['mid'] = (df[price_col_high].astype(float) + df[price_col_low].astype(float)) / 2.0
    else:
        # Fall back to any available column
        pcol = price_col_high if price_col_high in df else price_col_low
        df['mid'] = df[pcol].astype(float)

    df['SMA7'] = df['mid'].rolling(7, min_periods=1).mean()
    df['SMA30'] = df['mid'].rolling(30, min_periods=1).mean()

    # RSI(14)
    delta = df['mid'].diff()
    up = np.where(delta > 0, delta, 0.0)
    down = np.where(delta < 0, -delta, 0.0)
    roll_up = pd.Series(up, index=df.index).rolling(14, min_periods=14).mean()
    roll_down = pd.Series(down, index=df.index).rolling(14, min_periods=14).mean()
    rs = roll_up / (roll_down.replace(0, np.nan))
    df['RSI14'] = 100.0 - (100.0 / (1.0 + rs))
    df['RSI14'] = df['RSI14'].fillna(method='bfill').fillna(method='ffill')

    return df

def compute_signals(df: pd.DataFrame):
    """Return a small DataFrame with latest signals based on SMA crossovers and RSI."""
    if df.empty or 'SMA7' not in df or 'SMA30' not in df or 'RSI14' not in df:
        return pd.DataFrame()

    latest = df.tail(2).copy()
    if len(latest) < 2:
        return pd.DataFrame()

    prev, curr = latest.iloc[0], latest.iloc[1]
    signals = []

    # SMA crossover
    if prev['SMA7'] <= prev['SMA30'] and curr['SMA7'] > curr['SMA30']:
        signals.append(('SMA crossover', 'Bullish (SMA7 crossed above SMA30)', 'BUY'))
    elif prev['SMA7'] >= prev['SMA30'] and curr['SMA7'] < curr['SMA30']:
        signals.append(('SMA crossover', 'Bearish (SMA7 crossed below SMA30)', 'SELL'))
    else:
        signals.append(('SMA crossover', 'No crossover', 'HOLD'))

    # RSI zones
    rsi = curr['RSI14']
    if rsi < 30:
        signals.append(('RSI(14)', f'Oversold ({rsi:.1f})', 'BUY'))
    elif rsi > 70:
        signals.append(('RSI(14)', f'Overbought ({rsi:.1f})', 'SELL'))
    else:
        signals.append(('RSI(14)', f'Neutral ({rsi:.1f})', 'HOLD'))

    out = pd.DataFrame(signals, columns=['Indicator', 'Status', 'Action'])
    return out
