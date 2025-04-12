import praw
import pandas as pd
import time
import re
from datetime import datetime
import string
import spacy
import os
from glob import glob

nlp = spacy.load("en_core_web_sm")

# --- Reddit API setup ---

reddit = praw.Reddit(
    client_id = os.getenv("REDDIT_CLIENT_ID"),
    client_secret = os.getenv("REDDIT_SECRET"),
    user_agent = os.getenv("REDDIT_USER_AGENT")
)

def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    text = re.sub(r'[\n\r]', ' ', text)
    text = re.sub(r'&\w+;', '', text)
    text = re.sub(r'[^a-z\s]', '', text)

    doc = nlp(text)
    tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
    return ' '.join(tokens)

def get_pinned_posts(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    pinned = []
    for submission in subreddit.hot(limit=10):
        if submission.stickied:
            pinned.append(submission)
    return pinned

def get_comments(submission, seen_comment_ids):
    submission.comments.replace_more(limit=0)
    comments = []
    for comment in submission.comments.list():
        if comment.id in seen_comment_ids:
            continue  # Skip duplicate
        clean_body = clean_text(comment.body)
        comments.append({
            'comment_id': comment.id,
            'post_id': submission.id,
            'author': str(comment.author),
            'raw_body': comment.body,
            'clean_body': clean_body,
            'score': comment.score,
            'created_utc': datetime.utcfromtimestamp(comment.created_utc)
        })
    return comments

def get_seen_comment_ids():
    csv_files = sorted(glob("wsb_comments_*.csv"))
    if not csv_files:
        return set()
    latest_file = csv_files[-1]
    df = pd.read_csv(latest_file)
    return set(df['comment_id'].dropna().unique())

def main():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"wsb_comments_{timestamp}.csv"

    seen_comment_ids = get_seen_comment_ids()
    print(f"Loaded {len(seen_comment_ids)} previously seen comments.")

    all_comments = []
    pinned_posts = get_pinned_posts('wallstreetbets')
    print(f"Found {len(pinned_posts)} pinned posts.")

    for post in pinned_posts:
        print(f"Fetching comments for post: {post.title}")
        comments = get_comments(post, seen_comment_ids)
        print(f" - Retrieved {len(comments)} new comments")
        all_comments.extend(comments)
        time.sleep(2)

    df = pd.DataFrame(all_comments)
    df.to_csv(filename, index=False)
    print(f"Export complete: {filename}")

if __name__ == "__main__":
    main()
