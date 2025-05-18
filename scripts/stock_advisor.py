# import pandas as pd
# from backtest import backtest  # <-- your backtest function

# def load_combined_data(csv_path='output/combined_data.csv'):
#     df = pd.read_csv(csv_path)
#     if 'ma50' not in df.columns and 'symbol' in df.columns:
#         df['ma50'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(window=50, min_periods=1).mean())
#     return df

# def filter_stocks(df):
#     print(f"🔢 Initial stocks: {len(df)}")
#     df = df[df['avg_sentiment'] > 0.2]
#     print(f"📰 After sentiment filter: {len(df)}")
#     df = df[(df['rsi'] > 20) & (df['rsi'] < 80)]
#     print(f"📊 After RSI filter: {len(df)}")
#     df = df[df['macd'] > 0]
#     print(f"📈 After MACD filter: {len(df)}")
#     df = df[df['close'] > (df['ma50'] * 0.98)]
#     print(f"📉 After MA50 filter: {len(df)}")
#     return df

# def calculate_target_price(df, return_pct=10):
#     df['target_price'] = df['close'] * (1 + return_pct / 100)
#     return df

# def recommend_stocks():
#     df = load_combined_data()
#     filtered = filter_stocks(df)

#     if filtered.empty:
#         print("⚠️ No stocks match the criteria currently.")
#         return

#     symbols = filtered['symbol'].unique().tolist()
#     print(f"🔄 Backtesting {len(symbols)} filtered stocks in batches of 50...")

#     batch_size = 50
#     all_backtest_results = []

#     for i in range(0, len(symbols), batch_size):
#         batch = symbols[i:i + batch_size]
#         print(f"⏳ Backtesting batch {i // batch_size + 1} ({len(batch)} stocks)...")
#         batch_results = backtest(batch)  # your existing backtest function
#         if batch_results.empty:
#             print(f"⚠️ Backtest returned no results for batch {i // batch_size + 1}")
#             continue
#         all_backtest_results.append(batch_results)

#     if not all_backtest_results:
#         print("⚠️ No backtest results obtained.")
#         return

#     backtest_results = pd.concat(all_backtest_results, ignore_index=True)

#     # Verify required columns exist before filtering
#     required_cols = {'symbol', 'return_30d', 'max_drawdown', 'win_rate'}
#     missing = required_cols - set(backtest_results.columns)
#     if missing:
#         print(f"❌ Missing columns in backtest results: {missing}")
#         return

#     # Filter winners by backtest criteria
#     winners = backtest_results[
#         (backtest_results['return_30d'] >= 10) &
#         (backtest_results['max_drawdown'] <= 5) &
#         (backtest_results['win_rate'] >= 60)
#     ]

#     print(f"🎯 Stocks passing backtest: {len(winners)}")

#     if winners.empty:
#         print("⚠️ No stocks passed the backtest criteria.")
#         return

#     final_picks = filtered[filtered['symbol'].isin(winners['symbol'])]
#     final_picks = calculate_target_price(final_picks)

#     final_picks = final_picks.sort_values(by=['avg_sentiment', 'macd'], ascending=False)

#     final_picks.to_csv('output/backtested_picks.csv', index=False)
#     print("✅ Saved backtested picks to output/backtested_picks.csv")

#     cols_to_show = ['symbol', 'close', 'target_price', 'avg_sentiment', 'rsi', 'macd']
#     print("\n🚀 Final stock picks after backtest:\n")
#     print(final_picks[cols_to_show].head(15).to_string(index=False))


# if __name__ == "__main__":
#     recommend_stocks()


import pandas as pd
from backtest import backtest  # Your updated backtest function

def load_combined_data(csv_path='output/combined_data.csv'):
    df = pd.read_csv(csv_path)
    if 'ma50' not in df.columns and 'symbol' in df.columns:
        df['ma50'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(window=50, min_periods=1).mean())
    return df

def filter_stocks(df):
    print(f"🔢 Initial stocks: {len(df)}")
    df = df[df['avg_sentiment'] > 0.2]
    print(f"📰 After sentiment filter: {len(df)}")
    df = df[(df['rsi'] > 20) & (df['rsi'] < 80)]
    print(f"📊 After RSI filter: {len(df)}")
    df = df[df['macd'] > 0]
    print(f"📈 After MACD filter: {len(df)}")
    df = df[df['close'] > (df['ma50'] * 0.98)]
    print(f"📉 After MA50 filter: {len(df)}")
    return df

def calculate_target_price(df, return_pct=10):
    df['target_price'] = df['close'] * (1 + return_pct / 100)
    return df

def recommend_stocks():
    df = load_combined_data()
    filtered = filter_stocks(df)

    if filtered.empty:
        print("⚠️ No stocks match the criteria currently.")
        return

    symbols = filtered['symbol'].unique().tolist()
    print(f"🔄 Backtesting {len(symbols)} filtered stocks in batches of 50...")

    batch_size = 50
    all_backtest_results = []

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        print(f"⏳ Backtesting batch {i // batch_size + 1} ({len(batch)} stocks)...")
        batch_results = backtest(batch)
        if batch_results.empty:
            print(f"⚠️ Backtest returned no results for batch {i // batch_size + 1}")
            continue
        all_backtest_results.append(batch_results)

    if not all_backtest_results:
        print("⚠️ No backtest results obtained.")
        return

    backtest_results = pd.concat(all_backtest_results, ignore_index=True)

    # Check columns
    required_cols = {'symbol', 'return_30d', 'max_drawdown', 'win_rate', 'sharpe_ratio', 'sortino_ratio'}
    missing = required_cols - set(backtest_results.columns)
    if missing:
        print(f"❌ Missing columns in backtest results: {missing}")
        return

    # Filter winners by enhanced criteria
    winners = backtest_results[
        (backtest_results['return_30d'] >= 10) &
        (backtest_results['max_drawdown'] <= 5) &
        (backtest_results['win_rate'] >= 60) &
        (backtest_results['sharpe_ratio'] >= 1) &            # Sharpe > 1 for quality
        (backtest_results['sortino_ratio'] >= 1)             # Sortino > 1 for downside protection
    ]

    print(f"🎯 Stocks passing enhanced backtest: {len(winners)}")

    if winners.empty:
        print("⚠️ No stocks passed the enhanced backtest criteria.")
        return

    final_picks = filtered[filtered['symbol'].isin(winners['symbol'])]
    final_picks = calculate_target_price(final_picks)

    final_picks = final_picks.sort_values(by=['avg_sentiment', 'macd'], ascending=False)

    final_picks.to_csv('output/backtested_picks.csv', index=False)
    print("✅ Saved backtested picks to output/backtested_picks.csv")

    cols_to_show = ['symbol', 'close', 'target_price', 'avg_sentiment', 'rsi', 'macd']
    print("\n🚀 Final stock picks after enhanced backtest:\n")
    print(final_picks[cols_to_show].head(15).to_string(index=False))


if __name__ == "__main__":
    recommend_stocks()
