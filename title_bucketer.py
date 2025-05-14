# title_bucketer.py
import os
import json
import numpy as np
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Path to your buckets datastore
BUCKET_FILE = "buckets.json"

# Cosine-similarity threshold for “matching” an existing bucket
THRESHOLD = 0.8

def load_buckets():
    """Load existing buckets or return empty list if none."""
    try:
        with open(BUCKET_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_buckets(buckets):
    """Save updated buckets back to disk."""
    with open(BUCKET_FILE, "w") as f:
        json.dump(buckets, f, indent=2)

def classify_title(title: str):
    """
    Given a raw title string, returns (bucket_name, confidence).
    Creates a new bucket if no good match is found.
    """
    buckets = load_buckets()

    # 1) Embed the new title
    resp    = client.embeddings.create(
        model="text-embedding-3-small",
        input=title
    )
    new_emb = np.array(resp.data[0].embedding)

    # 2) Compare to each existing bucket
    best, best_score = None, -1.0
    for b in buckets:
        b_emb = np.array(b["embedding"])
        score = float(new_emb.dot(b_emb) /
                      (np.linalg.norm(new_emb) * np.linalg.norm(b_emb)))
        if score > best_score:
            best, best_score = b, score

    # 3) If it’s a strong match, use that bucket
    if best_score >= THRESHOLD:
        return best["bucket_name"], best_score

    # 4) Otherwise, create a new bucket entry
    new_bucket = {
        "bucket_name":    title,
        "title_examples": [title],
        "embedding":      new_emb.tolist()
    }
    buckets.append(new_bucket)
    save_buckets(buckets)
    return title, None
