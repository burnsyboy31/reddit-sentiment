import praw
import pandas as pd
import time
import re
from datetime import datetime
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
    return [s for s in subreddit.hot(limit=10) if s.stickied]

def get_comments(submission, seen_comment_ids):
    submission.comments.replace_more(limit=0)
    comments = []
    for comment in submission.comments.list():
        if comment.id in seen_comment_ids:
            continue
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

def load_master_csv(master_path):
    if os.path.exists(master_path):
        return pd.read_csv(master_path)
    else:
        return pd.DataFrame()

def main():
    master_path = "data/wsb_master_comments.csv"
    os.makedirs("data", exist_ok=True)

    existing_df = load_master_csv(master_path)
    seen_comment_ids = set(existing_df['comment_id'].dropna().unique())
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

    if not all_comments:
        print("✅ No new comments to add.")
        return

    new_df = pd.DataFrame(all_comments)
    combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=["comment_id"])

    combined_df.to_csv(master_path, index=False)
    print(f"✅ Master file updated: {master_path} — Total rows: {len(combined_df)}")

if __name__ == "__main__":
    main()
