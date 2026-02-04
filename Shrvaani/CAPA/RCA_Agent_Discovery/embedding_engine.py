import os
import requests
import numpy as np
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

HF_API_TOKEN = os.getenv("HF_Token")
MODEL_URL = "https://router.huggingface.co/hf-inference/models/BAAI/bge-small-en-v1.5"

HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

PHARMA_6M_DESCRIPTIONS = {
    "Manpower": "human factors training operator error aseptic technique gowning",
    "Machines": "filling line calibration autoclave HEPA filter sensor drift",
    "Methods": "SOP adherence sterilization parameters cleaning validation change control",
    "Materials": "stoppers vials seals filter compatibility WFI media quality supplier variability",
    "Measurements": "test method suitability incubation conditions sampling plan data integrity",
    "Environment": "HVAC pressure drift temperature humidity cleanroom grade personnel flow"
}

def get_embedding(text: str) -> np.ndarray:
    payload = {"inputs": text}
    response = requests.post(MODEL_URL, headers=HEADERS, json=payload, timeout=30)
    response.raise_for_status()
    arr = np.array(response.json())
    if arr.ndim == 2:
        return arr.mean(axis=0)
    return arr

# Initialize category embeddings
CATEGORY_EMBEDDINGS = {
    cat: get_embedding(desc) for cat, desc in PHARMA_6M_DESCRIPTIONS.items()
}

def map_to_6m(text: str):
    vec = get_embedding(text)
    scores = {}
    for cat, cat_vec in CATEGORY_EMBEDDINGS.items():
        score = cosine_similarity([vec], [cat_vec])[0][0]
        scores[cat] = round(float(score), 3)
    best_cat = max(scores, key=scores.get)
    return best_cat, scores
