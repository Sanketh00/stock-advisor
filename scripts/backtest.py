# import pandas as pd
# import yfinance as yf
# from datetime import datetime, timedelta

# def load_top_picks(filepath='output/top_picks.csv'):
#     df = pd.read_csv(filepath)
#     return df['symbol'].tolist()

# def backtest(stocks, return_target=0.10, lookback_days=30):
#     end_date = datetime.today()
#     start_date = end_date - timedelta(days=lookback_days)
#     results = []

#     for symbol in stocks:
#         ticker = symbol + '.NS'  # NSE suffix
#         print(f"⏳ Backtesting {symbol} as {ticker}...")

#         try:
#             df = yf.download(ticker,
#                              start=start_date.strftime('%Y-%m-%d'),
#                              end=end_date.strftime('%Y-%m-%d'),
#                              progress=False)

#             if df.empty:
#                 print(f"⚠️ No data for {symbol}")
#                 continue

#             # Flatten MultiIndex columns if present
#             if isinstance(df.columns, pd.MultiIndex):
#                 df.columns = [' '.join(col).strip() for col in df.columns.values]

#             close_col_name = f'Close {ticker}'

#             if close_col_name not in df.columns:
#                 print(f"⚠️ '{close_col_name}' column not found for {symbol}")
#                 continue

#             close_prices = df[close_col_name]

#             if close_prices.empty or close_prices.isnull().all():
#                 print(f"⚠️ 'Close' data invalid for {symbol}")
#                 continue

#             entry_price = close_prices.iloc[0]
#             max_close = close_prices.max()
#             final_price = close_prices.iloc[-1]

#             hit_target = max_close >= entry_price * (1 + return_target)
#             total_return = (final_price - entry_price) / entry_price

#             results.append({
#                 'symbol': symbol,
#                 'entry_price': round(entry_price, 2),
#                 'final_price': round(final_price, 2),
#                 'max_price': round(max_close, 2),
#                 'hit_10pct_target': hit_target,
#                 'total_return_pct': round(total_return * 100, 2)
#             })

#         except Exception as e:
#             print(f"❌ Error fetching data for {symbol}: {e}")

#     return pd.DataFrame(results)

# if __name__ == "__main__":
#     top_stocks = load_top_picks()
#     backtest_results = backtest(top_stocks)

#     if backtest_results.empty:
#         print("⚠️ No results to show.")
#     else:
#         print("\n📊 Backtest results for top 15 picks (last 30 days):\n")
#         print(backtest_results.head(15).to_string(index=False))

#         # Save results
#         backtest_results.to_csv('output/backtest_results.csv', index=False)
#         print("\n✅ Backtest results saved to output/backtest_results.csv")


# import pandas as pd
# import yfinance as yf
# from datetime import datetime, timedelta
# import numpy as np

# def backtest(stocks, return_target=0.10, lookback_days=30):
#     end_date = datetime.today()
#     start_date = end_date - timedelta(days=lookback_days)
#     results = []

#     for symbol in stocks:
#         ticker = symbol + '.NS'
#         print(f"⏳ Backtesting {symbol} as {ticker}...")

#         try:
#             df = yf.download(ticker,
#                              start=start_date.strftime('%Y-%m-%d'),
#                              end=end_date.strftime('%Y-%m-%d'),
#                              progress=False)

#             if df.empty:
#                 print(f"⚠️ No data for {symbol}")
#                 continue

#             # Flatten MultiIndex columns if present
#             if isinstance(df.columns, pd.MultiIndex):
#                 df.columns = [' '.join(col).strip() for col in df.columns.values]

#             close_col_name = f'Close {ticker}'

#             if close_col_name not in df.columns:
#                 print(f"⚠️ '{close_col_name}' column not found for {symbol}")
#                 continue

#             close_prices = df[close_col_name]

#             if close_prices.empty or close_prices.isnull().all():
#                 print(f"⚠️ 'Close' data invalid for {symbol}")
#                 continue

#             entry_price = close_prices.iloc[0]
#             final_price = close_prices.iloc[-1]
#             max_close = close_prices.max()

#             # Calculate return 30d
#             return_30d = (final_price - entry_price) / entry_price * 100

#             # Calculate max drawdown
#             cumulative_max = close_prices.cummax()
#             drawdowns = (close_prices - cumulative_max) / cumulative_max
#             max_drawdown = drawdowns.min() * 100  # negative number

#             # Calculate win rate (percentage of days price went up)
#             daily_returns = close_prices.pct_change().dropna()
#             win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100

#             hit_target = max_close >= entry_price * (1 + return_target)

#             results.append({
#                 'symbol': symbol,
#                 'entry_price': round(entry_price, 2),
#                 'final_price': round(final_price, 2),
#                 'max_price': round(max_close, 2),
#                 'hit_10pct_target': hit_target,
#                 'total_return_pct': round(return_30d, 2),
#                 'return_30d': round(return_30d, 2),
#                 'max_drawdown': round(abs(max_drawdown), 2),  # absolute value to match filter <=5%
#                 'win_rate': round(win_rate, 2)
#             })

#         except Exception as e:
#             print(f"❌ Error fetching data for {symbol}: {e}")

#     return pd.DataFrame(results)


import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np

def backtest(stocks, return_target=0.10, lookback_days=30):
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)
    results = []

    for symbol in stocks:
        ticker = symbol + '.NS'
        print(f"⏳ Backtesting {symbol} as {ticker}...")

        try:
            df = yf.download(ticker,
                             start=start_date.strftime('%Y-%m-%d'),
                             end=end_date.strftime('%Y-%m-%d'),
                             progress=False)

            if df.empty:
                print(f"⚠️ No data for {symbol}")
                continue

            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [' '.join(col).strip() for col in df.columns.values]

            close_col_name = f'Close {ticker}'
            if close_col_name not in df.columns:
                print(f"⚠️ '{close_col_name}' column not found for {symbol}")
                continue

            close_prices = df[close_col_name].dropna()
            if close_prices.empty:
                print(f"⚠️ 'Close' data invalid for {symbol}")
                continue

            entry_price = close_prices.iloc[0]
            final_price = close_prices.iloc[-1]
            max_close = close_prices.max()

            # Calculate return 30d (%)
            return_30d = (final_price - entry_price) / entry_price * 100

            # Max drawdown (%), absolute value
            cumulative_max = close_prices.cummax()
            drawdowns = (close_prices - cumulative_max) / cumulative_max
            max_drawdown = abs(drawdowns.min() * 100)

            # Daily returns
            daily_returns = close_prices.pct_change().dropna()
            if daily_returns.empty:
                print(f"⚠️ Insufficient daily returns for {symbol}")
                continue

            # Win rate (% of days price went up)
            win_rate = (daily_returns > 0).sum() / len(daily_returns) * 100

            # Volatility (std dev of daily returns) annualized
            volatility = daily_returns.std() * np.sqrt(252) * 100

            # Average daily return (%)
            avg_daily_return = daily_returns.mean() * 100

            # Sharpe Ratio assuming risk-free rate 0%
            sharpe_ratio = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252) if daily_returns.std() != 0 else np.nan

            # Sortino Ratio: downside deviation only
            negative_returns = daily_returns[daily_returns < 0]
            downside_std = negative_returns.std() if not negative_returns.empty else 0
            sortino_ratio = (daily_returns.mean() / downside_std) * np.sqrt(252) if downside_std != 0 else np.nan

            # Did it hit target return at any point?
            hit_target = max_close >= entry_price * (1 + return_target)

            results.append({
                'symbol': symbol,
                'entry_price': round(entry_price, 2),
                'final_price': round(final_price, 2),
                'max_price': round(max_close, 2),
                'hit_10pct_target': hit_target,
                'total_return_pct': round(return_30d, 2),
                'return_30d': round(return_30d, 2),
                'max_drawdown': round(max_drawdown, 2),
                'win_rate': round(win_rate, 2),
                'volatility_annual_pct': round(volatility, 2),
                'avg_daily_return_pct': round(avg_daily_return, 4),
                'sharpe_ratio': round(sharpe_ratio, 3) if not np.isnan(sharpe_ratio) else None,
                'sortino_ratio': round(sortino_ratio, 3) if not np.isnan(sortino_ratio) else None
            })

        except Exception as e:
            print(f"❌ Error fetching data for {symbol}: {e}")
    for result in results:
        print("result=",result)

    return pd.DataFrame(results)
