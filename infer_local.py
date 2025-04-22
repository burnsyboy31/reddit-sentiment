import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

# Paths
model_path = "/Users/zachburns/Desktop/Reddit_API/trained_model/content/reddit-roberta-final/" 
csv_path = "/Users/zachburns/Desktop/Reddit_API/trained_model/wsb_master_comments_04_21.csv"
output_path = "wsb_labeled_all.csv"

# Load model
tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True)
model.eval()

# Define label map
label_map = {0: "bullish", 1: "bearish", 2: "neutral"}

# Load all comments
df = pd.read_csv(csv_path)

# Batch predictions to avoid memory overload
BATCH_SIZE = 32
texts = df["raw_body"].tolist()
predictions = []

for i in range(0, len(texts), BATCH_SIZE):
    batch = texts[i:i + BATCH_SIZE]
    inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=128)
    with torch.no_grad():
        outputs = model(**inputs)
        preds = torch.argmax(outputs.logits, dim=1)
        predictions.extend(preds.tolist())

# Add predicted sentiment
df["sentiment_label"] = [label_map[i] for i in predictions]

# Save only required columns
df[["comment_id", "raw_body", "score", "sentiment_label","created_utc"]].to_csv(output_path, index=False)
print(f"✅ Labeled and saved all comments to: {output_path}")
