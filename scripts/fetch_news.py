import os
import pandas as pd
import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_news_rss(stock_name):
    query = stock_name.replace(' ', '%20') + '%20stock'
    url = f"https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
    feed = feedparser.parse(url)
    
    articles = []
    for entry in feed.entries[:10]:  # limit to 10 recent news
        title = entry.title
        articles.append(title)
    return articles

def analyze_sentiment(titles):
    analyzer = SentimentIntensityAnalyzer()
    scores = []
    for title in titles:
        vs = analyzer.polarity_scores(title)
        scores.append(vs['compound'])
    if scores:
        return sum(scores) / len(scores)
    else:
        return 0

def load_stock_list(csv_path='data/technical_snapshot.csv'):
    df = pd.read_csv(csv_path)
    return df['symbol'].dropna().astype(str).str.strip().tolist()

def fetch_sentiment_for_symbol(symbol):
    try:
        news_titles = fetch_news_rss(symbol)
        avg_sentiment = analyze_sentiment(news_titles)
        return {'symbol': symbol, 'avg_sentiment': round(avg_sentiment, 4), 'news_count': len(news_titles)}
    except Exception as e:
        print(f"❌ Error for {symbol}: {e}")
        return {'symbol': symbol, 'avg_sentiment': 0, 'news_count': 0}

if __name__ == "__main__":
    symbols = load_stock_list()
    results = []

    # Use max_workers=10 to fetch 10 stocks in parallel
    with ThreadPoolExecutor(max_workers=500) as executor:
        futures = [executor.submit(fetch_sentiment_for_symbol, s) for s in symbols]
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            print(f"[{i}/{len(symbols)}] Fetched {result['symbol']} | Sentiment: {result['avg_sentiment']} | News Count: {result['news_count']}")
            results.append(result)

    df = pd.DataFrame(results)

    # Create output directory if not exists
    os.makedirs('output', exist_ok=True)

    df.to_csv('output/stock_news_sentiment.csv', index=False)
    print("✅ Saved news sentiment to output/stock_news_sentiment.csv")
