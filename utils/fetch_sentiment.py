import praw
import pandas as pd
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Set up Reddit API credentials (replace with your actual credentials)
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET",
    user_agent="osrs-stockbot by /u/YOUR_USERNAME"
)

def fetch_reddit_sentiment(query="oathplate chest", subreddit="2007scape", limit=100):
    analyzer = SentimentIntensityAnalyzer()
    posts = []

    for submission in reddit.subreddit(subreddit).search(query, limit=limit):
        title = submission.title
        score = submission.score
        created_utc = datetime.utcfromtimestamp(submission.created_utc)

        sentiment = analyzer.polarity_scores(title)
        posts.append({
            "title": title,
            "score": score,
            "created": created_utc,
            "sentiment_compound": sentiment["compound"],
            "sentiment_pos": sentiment["pos"],
            "sentiment_neu": sentiment["neu"],
            "sentiment_neg": sentiment["neg"]
        })

    df = pd.DataFrame(posts)
    df.to_csv("data/sentiment/oathplate_sentiment.csv", index=False)
    return df

if __name__ == "__main__":
    df = fetch_reddit_sentiment()
    print(df.head())
