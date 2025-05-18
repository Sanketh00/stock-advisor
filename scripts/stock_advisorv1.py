import pandas as pd
from backtestv1 import backtest
import logging
import numpy as np
import time
# Setup logging
logging.basicConfig(level=logging.INFO, filename='stock_advisor.log', format='%(asctime)s - %(message)s')

def load_combined_data(csv_path='output/combined_data.csv'):
    logging.info("Loading combined_data.csv")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        logging.error(f"Failed to load combined_data.csv: {str(e)}")
        raise
    required_cols = ['symbol', 'close', 'avg_sentiment', 'rsi', 'macd']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logging.error(f"Missing columns in combined_data.csv: {missing_cols}")
        raise ValueError(f"Missing columns: {missing_cols}")
    df = df[df['rsi'].between(0, 100)]
    df = df[df['avg_sentiment'].between(-1, 1)]
    if 'ma50' not in df.columns and 'symbol' in df.columns:
        df['ma50'] = df.groupby('symbol')['close'].transform(lambda x: x.rolling(window=50, min_periods=1).mean())
    logging.info(f"Loaded {len(df)} rows, {len(df['symbol'].unique())} unique symbols")
    return df

def filter_stocks(df):
    logging.info(f"Initial stocks: {len(df['symbol'].unique())}")
    df = df[df['avg_sentiment'] > 0.2]  # Relaxed sentiment
    logging.info(f"After sentiment filter (>0.2): {len(df['symbol'].unique())}")
    df = df[(df['rsi'] >= 40) & (df['rsi'] <= 75)]  # Relaxed RSI
    logging.info(f"After RSI filter (40–75): {len(df['symbol'].unique())}")
    df = df[df['macd'] > 0]
    logging.info(f"After MACD filter (>0): {len(df['symbol'].unique())}")
    df = df[df['close'] > (df['ma50'] * 0.98)] # Relaxed momentum
    logging.info(f"After MA50 filter (>MA50): {len(df['symbol'].unique())}")
    return df

def calculate_target_price(df, return_pct=10):
    df.loc[:, 'target_price'] = df['entry_price'] * (1 + return_pct / 100)
    return df

def calculate_confidence(df):
    """Calculate confidence score based on RSI, sentiment, and bullish engulfing."""
    df['rsi_score'] = (df['rsi'] - 40) / 35  # Normalize RSI 40–75 to 0–1
    df['sentiment_score'] = (df['avg_sentiment'] - 0.2) / 0.8  # Normalize 0.2–1 to 0–1
    df['engulfing_score'] = df['bullish_engulfing_count'] / df['bullish_engulfing_count'].max() if df['bullish_engulfing_count'].max() > 0 else 0
    df['confidence'] = (df['rsi_score'] + df['sentiment_score'] + df['engulfing_score']) / 3
    return df

def recommend_stocks(max_stocks=300):
    start_time = time.time()
    df = load_combined_data()
    filtered = filter_stocks(df)

    if filtered.empty:
        logging.warning("No stocks match the initial criteria.")
        print("⚠️ No stocks match the initial criteria.")
        return

    symbols = filtered['symbol'].unique().tolist()[:max_stocks]
    logging.info(f"Backtesting {len(symbols)} filtered stocks in batches of 50...")

    batch_size = 50
    all_backtest_results = []

    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        logging.info(f"Backtesting batch {i // batch_size + 1} ({len(batch)} stocks)...")
        batch_results = backtest(batch)
        if batch_results.empty:
            logging.warning(f"Backtest returned no results for batch {i // batch_size + 1}")
            continue
        logging.info(f"Batch {i // batch_size + 1} results: {len(batch_results)} stocks")
        all_backtest_results.append(batch_results)

    if not all_backtest_results:
        logging.warning("No backtest results obtained.")
        print("⚠️ No backtest results obtained.")
        return

    backtest_results = pd.concat(all_backtest_results, ignore_index=True)
    logging.info(f"Combined backtest results: {len(backtest_results)} stocks, columns: {list(backtest_results.columns)}")

    required_cols = {'symbol', 'return_30d', 'breakout_detected', 'bullish_engulfing_count', 'breakout_success', 'entry_price', 'exit_price', 'exit_reason'}
    missing = required_cols - set(backtest_results.columns)
    if missing:
        logging.error(f"Missing columns in backtest results: {missing}")
        print(f"❌ Missing columns: {missing}")
        return

    winners = backtest_results[
        (backtest_results['return_30d'] >= 10) &
        (backtest_results['breakout_detected'] == True) &
        (backtest_results['bullish_engulfing_count'] >= 1) &
        (backtest_results['breakout_success'] == True)
    ]

    logging.info(f"Stocks passing backtest for >10% return potential: {len(winners)}")

    if winners.empty:
        logging.warning("No stocks passed the backtest criteria.")
        print("⚠️ No stocks passed the backtest criteria.")
        return

    final_picks = filtered[filtered['symbol'].isin(winners['symbol'])].copy()
    final_picks = final_picks.merge(
        winners[['symbol', 'entry_price', 'exit_price', 'exit_reason', 'breakout_success', 'bullish_engulfing_count', 'return_30d']],
        on='symbol',
        how='inner'
    )

    # Relaxed momentum filter
    final_picks = final_picks[final_picks['close'] > (final_picks['ma50'] * 0.98)]
    logging.info(f"After momentum filter (>MA50): {len(final_picks)} stocks")

    if final_picks.empty:
        logging.warning("No stocks passed the momentum filter.")
        print("⚠️ No stocks passed the momentum filter.")
        return

    final_picks = calculate_target_price(final_picks)
    final_picks = calculate_confidence(final_picks)

    logging.info(f"Final picks columns: {list(final_picks.columns)}")
    final_picks = final_picks.sort_values(by=['confidence', 'return_30d', 'avg_sentiment'], ascending=False)

    final_picks.to_csv('output/backtested_picks.csv', index=False)
    logging.info("Saved backtested picks to output/backtested_picks.csv")

    cols_to_show = ['symbol', 'close', 'entry_price', 'target_price', 'exit_reason', 'avg_sentiment', 'rsi', 'macd', 'bullish_engulfing_count', 'breakout_success', 'return_30d', 'confidence']
    print("\n🚀 Stock picks with >10% return potential in next 30 days:\n")
    print(final_picks[cols_to_show].head(15).to_string(index=False))
    logging.info(f"Script completed in {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    recommend_stocks()