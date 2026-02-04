# embedding_mapper.py

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

SIX_M_DESCRIPTIONS = {
    "Man": "human factors, training issues, operator error, misuse",
    "Machine": "device hardware, firmware, software, equipment malfunction",
    "Method": "procedures, SOPs, workflow, process issues",
    "Material": "components, raw materials, supplier quality",
    "Measurement": "testing methods, calibration, inspection accuracy",
    "Environment": "temperature, humidity, electromagnetic interference"
}


def embed(text: str):
    np.random.seed(abs(hash(text)) % (10**6))
    return np.random.rand(384)


def map_cause_to_6m(cause_text: str):
    cause_vec = embed(cause_text)

    scores = {}
    for category, desc in SIX_M_DESCRIPTIONS.items():
        cat_vec = embed(desc)
        score = cosine_similarity(
            cause_vec.reshape(1, -1),
            cat_vec.reshape(1, -1)
        )[0][0]
        scores[category] = round(float(score), 3)

    best_category = max(scores, key=scores.get)

    return best_category, scores
