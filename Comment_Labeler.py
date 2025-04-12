from openai import OpenAI
import pandas as pd
import time
from tqdm import tqdm
import os

from dotenv import load_dotenv
load_dotenv()


# Set API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Load data
df = pd.read_csv("wsb_cleaned_comments.csv")
df = df.dropna(subset=['raw_body']).reset_index(drop=True)

# Limit if testing
# df = df.sample(50)


def classify_comment(comment):
    prompt = (
        "You're a financial analyst. Classify the following Reddit comment "
        "as one of the following sentiment labels regarding the stock market: "
        "**bullish**, **bearish**, or **neutral**. "
        "Respond with ONLY the label.\n\n"
        f"{comment}"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=10,
        )
        return response.choices[0].message.content.strip().lower()
    except Exception as e:
        print(f"Error: {e}")
        return "error"

# Loop through comments and classify
labels = []
for comment in tqdm(df['raw_body']):
    label = classify_comment(comment)
    labels.append(label)
    time.sleep(1.2)  # Stay below rate limit

df['sentiment_label'] = labels
df.to_csv("wsb_labeled_comments.csv", index=False)
print("Labeling complete. Saved to wsb_labeled_comments.csv")

