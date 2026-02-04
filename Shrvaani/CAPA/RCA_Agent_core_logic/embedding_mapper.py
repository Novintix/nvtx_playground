import os
from dotenv import load_dotenv
import requests
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables
load_dotenv()

HF_API_TOKEN = os.getenv("HF_Token")

# New Hugging Face Router URL
MODEL_URL = "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5"

HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

SIX_M_DESCRIPTIONS = {
    "Man": "human factors training operator error misuse",
    "Machine": "device hardware firmware software equipment malfunction",
    "Method": "procedures SOP workflow process issues",
    "Material": "components raw materials supplier quality",
    "Measurement": "testing calibration inspection accuracy",
    "Environment": "temperature humidity electromagnetic interference"
}


def embed(text: str) -> np.ndarray:
    payload = {"inputs": text}

    response = requests.post(
        MODEL_URL,
        headers=HEADERS,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    result = response.json()

    # HF returns either:
    # - list[list[float]] (token embeddings)
    # - or list[float] (sentence embedding)
    arr = np.array(result)

    if arr.ndim == 2:
        return arr.mean(axis=0)  # mean pooling
    return arr


# Cache category embeddings at startup
CATEGORY_EMBEDDINGS = {
    category: embed(desc)
    for category, desc in SIX_M_DESCRIPTIONS.items()
}


def map_cause_to_6m(cause_text: str):
    cause_vec = embed(cause_text)

    scores = {}
    for category, cat_vec in CATEGORY_EMBEDDINGS.items():
        score = cosine_similarity(
            [cause_vec],
            [cat_vec]
        )[0][0]
        scores[category] = round(float(score), 3)

    best_category = max(scores, key=scores.get)
    return best_category, scores
