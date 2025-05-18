import os
import pandas as pd

def combine_technical_and_sentiment(
    tech_csv='data/technical_snapshot.csv',
    sentiment_csv='output/stock_news_sentiment.csv'
):
    # Check if technical CSV exists
    if not os.path.exists(tech_csv):
        print(f"❌ Technical data file not found: {tech_csv}")
        print("Please check the path or generate the technical data CSV first.")
        return

    # Check if sentiment CSV exists
    if not os.path.exists(sentiment_csv):
        print(f"❌ Sentiment data file not found: {sentiment_csv}")
        print("Please run the sentiment fetch script first.")
        return

    # Load data
    df_tech = pd.read_csv(tech_csv)
    df_sentiment = pd.read_csv(sentiment_csv)

    # Standardize column names to lowercase & strip spaces
    df_tech.rename(columns=lambda x: x.strip().lower(), inplace=True)
    df_sentiment.rename(columns=lambda x: x.strip().lower(), inplace=True)

    # Merge on 'symbol'
    if 'symbol' not in df_tech.columns or 'symbol' not in df_sentiment.columns:
        print("❌ 'symbol' column missing in one of the CSVs.")
        return

    df_merged = pd.merge(df_tech, df_sentiment, on='symbol', how='inner')

    # Ensure output folder exists
    os.makedirs('output', exist_ok=True)

    # Save merged CSV
    merged_csv_path = 'output/combined_data.csv'
    df_merged.to_csv(merged_csv_path, index=False)
    print(f"✅ Combined data saved to {merged_csv_path}")

if __name__ == "__main__":
    # Update these paths if your filenames are different
    combine_technical_and_sentiment(
        tech_csv='data/technical_snapshot.csv',
        sentiment_csv='output/stock_news_sentiment.csv'
    )
