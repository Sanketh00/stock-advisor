import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator

def calculate_indicators(df):
    df = df.copy()  # avoid SettingWithCopyWarning

    # Ensure no missing close prices before indicators
    df.dropna(subset=['Close'], inplace=True)
    close = df['Close']

    rsi = RSIIndicator(close=close).rsi()
    macd_diff = MACD(close=close).macd_diff()
    sma20 = SMAIndicator(close=close, window=20).sma_indicator()

    # Use .loc to avoid warnings
    df.loc[:, 'rsi'] = rsi
    df.loc[:, 'macd'] = macd_diff
    df.loc[:, 'sma20'] = sma20

    df.dropna(subset=['rsi', 'macd', 'sma20'], inplace=True)
    return df

def fetch_all_technicals(symbols):
    tickers = ' '.join([s + '.NS' for s in symbols])
    print(f"Fetching batch for {len(symbols)} symbols...")

    data = yf.download(
        tickers,
        period='60d',
        interval='1d',
        group_by='ticker',
        auto_adjust=True,
        progress=False
    )

    results = []
    for symbol in symbols:
        try:
            df = data[symbol + '.NS']
            df = calculate_indicators(df)
            if df.empty:
                print(f"⚠️ No usable data for {symbol}")
                continue
            latest = df.iloc[-1]
            results.append({
                'symbol': symbol,
                'date': latest.name.date(),
                'close': round(latest['Close'], 2),
                'rsi': round(latest['rsi'], 2),
                'macd': round(latest['macd'], 2),
                'sma20': round(latest['sma20'], 2)
            })
        except Exception as e:
            print(f"❌ Error for {symbol}: {e}")

    return results

def load_stock_list(csv_path='nifty500.csv'):
    df = pd.read_csv(csv_path)
    return df['Symbol'].dropna().astype(str).str.strip().tolist()

if __name__ == "__main__":
    symbols = load_stock_list()

    chunk_size = 50
    all_results = []

    for i in range(0, len(symbols), chunk_size):
        batch = symbols[i:i + chunk_size]
        batch_results = fetch_all_technicals(batch)
        all_results.extend(batch_results)

    df_final = pd.DataFrame(all_results)
    df_final.to_csv("data/technical_snapshot.csv", index=False)
    print("✅ Saved to data/technical_snapshot.csv")
