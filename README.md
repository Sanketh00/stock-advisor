# 📈 Stock Advisor

A smart stock recommendation system that uses sentiment analysis, technical indicators (RSI, MACD, Moving Averages), and backtesting to suggest fundamentally and technically strong stocks.

## 🔧 Features

- ✅ Filters stocks using:
  - Sentiment score (based on news/social media)
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - 50-day Moving Average

- 🔍 Backtests with:
  - Return over 30 days
  - Max drawdown
  - Win rate
  - Sharpe and Sortino ratios

- 📊 Final picks include price targets and detailed metrics.

## 🗂️ Project Structure

<pre>
stock-advisor/
├── stock_advisor.py # Main recommendation script
├── backtest.py # Backtesting logic
├── output/ # Output CSVs
├── data/ # Symbol lists (e.g. Nifty500, Microcap250)
├── requirements.txt # Python dependencies
└── README.md # You're reading this
 </pre>


## 🚀 How to Run

1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/stock-advisor.git
   cd stock-advisor
   pip install -r requirements.txt
   python fetch_prices.py
   python fetch_news.py
   python stock_advisor.py


## ✨ To Do
1. Add live price tracker
2.  Integrate Telegram/Email alerts
3.   Deploy as a web app
