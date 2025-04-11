import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd

# --- Reddit API setup ---
reddit = praw.Reddit(
    client_id="LDWwnKfRexKaQYP5yH_4DA",          # Replace with your client ID
    client_secret="OFT7BJXhFMlDPfWQFYZNCK6RczK4BA",  # Replace with your client secret
    user_agent="sentiment-test-script-zb"   
)

# --- Sentiment analyzer setup ---
analyzer = SentimentIntensityAnalyzer()

# --- Pull top 5 posts from r/technology ---
subreddit = reddit.subreddit("technology")  # You can change this to another subreddit

# Create a list to store post details and sentiment scores
posts = []

for post in subreddit.hot(limit=5):
    title = post.title
    sentiment = analyzer.polarity_scores(title)["compound"]  # Get sentiment score
    posts.append({
        "title": title,
        "score": post.score,  # Post score (upvotes)
        "sentiment": sentiment  # Sentiment score
    })

# Convert the list of posts to a DataFrame
df = pd.DataFrame(posts)

# Print the DataFrame (or save it to a CSV)
print(df)

# Optionally, save it to a CSV
df.to_csv("reddit_sentiment.csv", index=False)
