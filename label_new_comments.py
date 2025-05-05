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

# === Load Master Data ===
df_master = pd.read_csv(master_file)

print(f"🔍 Relabeling all {len(df_master)} comments from master file.")

# === Predict Labels in Batches ===
label_map = {0: "bullish", 1: "bearish", 2: "neutral"}
texts = df_master["raw_body"].tolist()
batch_size = 32
predictions = []

for i in range(0, len(texts), batch_size):
    batch_texts = texts[i:i+batch_size]
    inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        preds = torch.argmax(outputs.logits, dim=1)
        predictions.extend(preds.tolist())

df_master["sentiment_label"] = [label_map[i] for i in predictions]

# === Keep Only Needed Columns ===
df_final = df_master[["comment_id", "raw_body", "score", "sentiment_label", "created_utc"]]

# === Save All Labeled Comments ===
df_final.to_csv(labeled_file, index=False)

print(f"✅ Relabeled all {len(df_final)} comments. Saved to {labeled_file}.")


