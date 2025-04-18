import praw
import pandas as pd
import time
import re
from datetime import datetime
import string
import spacy
nlp = spacy.load("en_core_web_sm")

# --- Reddit API setup ---
reddit = praw.Reddit(
    client_id="LDWwnKfRexKaQYP5yH_4DA",          # Replace with your client ID
    client_secret="OFT7BJXhFMlDPfWQFYZNCK6RczK4BA",  # Replace with your client secret
    user_agent="sentiment-test-script-zb"   
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

# Get pinned posts
def get_pinned_posts(subreddit_name):
    subreddit = reddit.subreddit(subreddit_name)
    pinned = []
    for submission in subreddit.hot(limit=10):
        if submission.stickied:
            pinned.append(submission)
    return pinned

# Get comments
def get_comments(submission):
    submission.comments.replace_more(limit=0)
    comments = []
    for comment in submission.comments.list():
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

# Main
def main():
    all_comments = []
    pinned_posts = get_pinned_posts('wallstreetbets')
    print(f"Found {len(pinned_posts)} pinned posts.")

    for post in pinned_posts:
        print(f"Fetching comments for post: {post.title}")
        comments = get_comments(post)
        print(f" - Retrieved {len(comments)} comments")
        all_comments.extend(comments)
        time.sleep(2)  # Respect rate limit

    df = pd.DataFrame(all_comments)
    df.to_csv('wsb_cleaned_comments.csv', index=False)
    print("Export complete: wsb_cleaned_comments.csv")

if __name__ == "__main__":
    main()