import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import time
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO, filename='backtest.log', format='%(asctime)s - %(message)s')

def detect_bullish_engulfing(df, close_col, open_col, prev_close_col, prev_open_col):
    """Detect bullish engulfing pattern."""
    bullish = (df[close_col] > df[open_col])
    prev_bearish = (df[prev_close_col] < df[prev_open_col])
    engulfing = (df[close_col] > df[prev_open_col]) & (df[open_col] < df[prev_close_col])
    return bullish & prev_bearish & engulfing

def find_support_resistance(df, close_col, window=10):
    """Identify support and resistance."""
    support = df['Low'].rolling(window=window, min_periods=1).min()
    resistance = df['High'].rolling(window=window, min_periods=1).max()
    return support, resistance

def fetch_batch_data(tickers, start_date, end_date, retries=2, delay=2, timeout=30):
    """Fetch data for multiple tickers with timeout, handling cache robustly."""
    cache_file = 'output/yfinance_cache.csv'
    
    # Try loading cached data
    if os.path.exists(cache_file):
        try:
            logging.info("Attempting to load cached yfinance data")
            df = pd.read_csv(cache_file)
            
            # Check for date-like column (case-insensitive)
            date_cols = [col for col in df.columns if col.lower() in ['date', 'index']]
            if date_cols:
                df = df.set_index(date_cols[0])
                df.index = pd.to_datetime(df.index, format='%Y-%m-%d')
            else:
                # Try using first column as index
                df = pd.read_csv(cache_file, index_col=0, parse_dates=True, date_format='%Y-%m-%d')
            
            # Verify required columns for at least one ticker
            required_cols = ['Close', 'Open', 'High', 'Low', 'Volume']
            if any(col in df.columns for col in required_cols):
                logging.info("Successfully loaded cached data")
                return df
            else:
                logging.warning("Cached data missing required columns, fetching fresh data")
        except Exception as e:
            logging.warning(f"Failed to load cached data: {str(e)}, fetching fresh data")
    
    # Fetch fresh data
    for attempt in range(retries):
        try:
            data = yf.download(tickers, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False, group_by='ticker', timeout=timeout, auto_adjust=True)
            if not data.empty:
                # Save with clear index
                data.to_csv(cache_file, index_label='Date')
                logging.info("Saved fresh yfinance data to cache")
            return data
        except Exception as e:
            logging.warning(f"Batch fetch failed on attempt {attempt + 1}: {str(e)}")
            if attempt < retries - 1:
                time.sleep(delay)
    logging.error("Failed to fetch data after retries")
    return pd.DataFrame()

def rename_columns(df, ticker):
    """Rename columns to standard names."""
    column_map = {}
    for col in df.columns:
        col_str = str(col).strip()
        for standard_col in ['Close', 'Open', 'High', 'Low', 'Volume']:
            if standard_col in col_str:
                column_map[col] = standard_col
                break
    return df.rename(columns=column_map)

def backtest(stocks, return_target=0.10, lookback_days=30):
    start_time = time.time()
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)
    results = []
    skipped_stocks = []

    tickers = [s + '.NS' for s in stocks]
    logging.info(f"Fetching data for {len(tickers)} tickers...")
    data = fetch_batch_data(tickers, start_date, end_date)
    if data.empty:
        logging.warning("No data fetched for any tickers")
        return pd.DataFrame(columns=['symbol', 'entry_price', 'final_price', 'max_price', 'exit_price', 'exit_reason', 'hit_10pct_target', 'breakout_detected', 'breakout_success', 'bullish_engulfing_count', 'total_return_pct', 'return_30d', 'max_drawdown', 'win_rate', 'volatility_annual_pct', 'avg_daily_return_pct', 'sharpe_ratio', 'sortino_ratio'])

    for symbol in stocks:
        ticker = symbol + '.NS'
        logging.info(f"Backtesting {symbol}...")

        result = {
            'symbol': symbol,
            'entry_price': None,
            'final_price': None,
            'max_price': None,
            'exit_price': None,
            'exit_reason': None,
            'hit_10pct_target': False,
            'breakout_detected': False,
            'breakout_success': False,
            'bullish_engulfing_count': 0,
            'total_return_pct': None,
            'return_30d': None,
            'max_drawdown': None,
            'win_rate': None,
            'volatility_annual_pct': None,
            'avg_daily_return_pct': None,
            'sharpe_ratio': None,
            'sortino_ratio': None
        }

        try:
            if ticker in data:
                df = data[ticker].copy()
            else:
                logging.warning(f"No data for {symbol}")
                skipped_stocks.append(symbol)
                results.append(result)
                continue

            required_cols = ['Close', 'Open', 'High', 'Low', 'Volume']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logging.warning(f"Missing columns for {symbol}: {missing_cols}")
                skipped_stocks.append(symbol)
                results.append(result)
                continue

            df = df.dropna()
            if len(df) < 2:
                logging.warning(f"Insufficient data for {symbol} (only {len(df)} rows)")
                skipped_stocks.append(symbol)
                results.append(result)
                continue

            logging.info(f"Data for {symbol}: shape={df.shape}, columns={list(df.columns)}")

            df['prev_close'] = df['Close'].shift(1)
            df['prev_open'] = df['Open'].shift(1)
            df['bullish_engulfing'] = detect_bullish_engulfing(
                df, 'Close', 'Open', 'prev_close', 'prev_open'
            )
            result['bullish_engulfing_count'] = df['bullish_engulfing'].sum()

            df['support'], df['resistance'] = find_support_resistance(df, 'Close')

            # Breakout with volume confirmation
            df['avg_volume'] = df['Volume'].rolling(window=20, min_periods=1).mean()
            highest_high = df['High'].rolling(window=lookback_days, min_periods=1).max()
            df['breakout'] = (df['Close'] > highest_high.shift(1)) & (df['Volume'] > df['avg_volume'] * 1.5)
            breakout_days = df[df['breakout']].index
            result['breakout_detected'] = len(breakout_days) > 0

            entry_price = None
            entry_date = None
            exit_price = None
            exit_date = None
            breakout_success = False
            exit_reason = None

            if not breakout_days.empty:
                entry_date = breakout_days[0]
                entry_price = df.loc[entry_date, 'Close']
                entry_idx = df.index.get_loc(entry_date)

                post_breakout = df.iloc[entry_idx:]
                target_price = entry_price * (1 + return_target)
                stop_loss = df.loc[entry_date, 'support'] * 0.98

                for date in post_breakout.index:
                    if post_breakout.loc[date, 'High'] >= target_price:
                        exit_price = target_price
                        exit_date = date
                        breakout_success = True
                        exit_reason = 'target_hit'
                        break
                    elif post_breakout.loc[date, 'Low'] <= stop_loss:
                        exit_price = stop_loss
                        exit_date = date
                        breakout_success = False
                        exit_reason = 'stop_loss'
                        break

                if exit_price is None:
                    exit_reason = 'no_exit'
                    breakout_success = False

            result['breakout_success'] = breakout_success
            result['entry_price'] = round(entry_price, 2) if entry_price else round(df['Close'].iloc[0], 2)
            result['exit_price'] = round(exit_price, 2) if exit_price else None
            result['exit_reason'] = exit_reason

            close_prices = df['Close']
            entry_price_calc = close_prices.iloc[0]
            final_price = close_prices.iloc[-1]
            max_close = close_prices.max()

            result['total_return_pct'] = round((final_price - entry_price_calc) / entry_price_calc * 100, 2)
            result['return_30d'] = result['total_return_pct']
            result['final_price'] = round(final_price, 2)
            result['max_price'] = round(max_close, 2)

            cumulative_max = close_prices.cummax()
            drawdowns = (close_prices - cumulative_max) / cumulative_max
            result['max_drawdown'] = round(abs(drawdowns.min() * 100), 2)

            daily_returns = close_prices.pct_change().dropna()
            if daily_returns.empty:
                logging.warning(f"Insufficient daily returns for {symbol}")
                skipped_stocks.append(symbol)
                results.append(result)
                continue

            result['win_rate'] = round((daily_returns > 0).sum() / len(daily_returns) * 100, 2)
            result['volatility_annual_pct'] = round(daily_returns.std() * np.sqrt(252) * 100, 2)
            result['avg_daily_return_pct'] = round(daily_returns.mean() * 100, 4)

            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() != 0 else np.nan
            result['sharpe_ratio'] = round(sharpe_ratio, 3) if not np.isnan(sharpe_ratio) else None

            negative_returns = daily_returns[daily_returns < 0]
            downside_std = negative_returns.std() if not negative_returns.empty else 0
            sortino_ratio = (daily_returns.mean() / downside_std) * np.sqrt(252) if downside_std != 0 else np.nan
            result['sortino_ratio'] = round(sortino_ratio, 3) if not np.isnan(sortino_ratio) else None

            result['hit_10pct_target'] = max_close >= entry_price_calc * (1 + return_target)

            results.append(result)

        except Exception as e:
            logging.error(f"Error processing {symbol}: {str(e)}")
            skipped_stocks.append(symbol)
            results.append(result)

    if skipped_stocks:
        logging.info(f"Skipped stocks: {skipped_stocks}")

    if not results:
        logging.warning("No backtest results generated")
        return pd.DataFrame(columns=['symbol', 'entry_price', 'final_price', 'max_price', 'exit_price', 'exit_reason', 'hit_10pct_target', 'breakout_detected', 'breakout_success', 'bullish_engulfing_count', 'total_return_pct', 'return_30d', 'max_drawdown', 'win_rate', 'volatility_annual_pct', 'avg_daily_return_pct', 'sharpe_ratio', 'sortino_ratio'])

    result_df = pd.DataFrame(results)
    logging.info(f"Backtest results columns: {list(result_df.columns)}")
    logging.info(f"Backtest completed in {time.time() - start_time:.2f} seconds")
    return result_df