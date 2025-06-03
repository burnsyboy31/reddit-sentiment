import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from huggingface_hub import login
import torch
import os

# === Hugging Face Auth ===
login(token=os.getenv("HF_TOKEN"))

# === Paths ===
model_path = "pbandjatairport/reddit-sentiment-v2"
master_file = "data/wsb_master_comments.csv"
labeled_file = "data/labeled_comments.csv"

# === Load Model ===
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForSequenceClassification.from_pretrained(model_path)
model.eval()

# === Load Master and Previous Labeled Data ===
df_master = pd.read_csv(master_file)
if os.path.exists(labeled_file):
    df_prev = pd.read_csv(labeled_file)
    seen_ids = set(df_prev['comment_id'])
else:
    df_prev = pd.DataFrame(columns=["comment_id", "raw_body", "score", "sentiment_label", "created_utc"])
    seen_ids = set()

# === Filter New Comments ===
df_new = df_master[~df_master['comment_id'].isin(seen_ids)].copy()
df_new = df_new.dropna(subset=["raw_body"]) 
if df_new.empty:
    print("✅ No new comments to label.")
    exit()

print(f"🔍 Found {len(df_new)} new comments to label.")

# === Predict Labels in Batches ===
label_map = {0: "bullish", 1: "bearish", 2: "neutral"}
texts = df_new["raw_body"].dropna().astype(str).tolist()
batch_size = 32
predictions = []

for i in range(0, len(texts), batch_size):
    batch_texts = texts[i:i+batch_size]
    inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        preds = torch.argmax(outputs.logits, dim=1)
        predictions.extend(preds.tolist())

df_new["sentiment_label"] = [label_map[i] for i in predictions]

# === Keep Only Needed Columns ===
df_new = df_new[["comment_id", "raw_body", "score", "sentiment_label", "created_utc"]]

# === Append and Save ===
df_final = pd.concat([df_prev, df_new], ignore_index=True)
df_final.to_csv(labeled_file, index=False)

print(f"✅ Labeled {len(df_new)} new comments. Saved to {labeled_file}.")

print(f"✅ Relabeled all {len(df_final)} comments. Saved to {labeled_file}.")


