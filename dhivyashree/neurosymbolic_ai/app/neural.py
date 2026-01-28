from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans
import numpy as np
from app.models import LogEntry

class LogClusterer:
    def __init__(self, n_clusters=5):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42)
        self.is_fitted = False

    def train(self, logs: List[str]):
        if not logs:
            return
        X = self.vectorizer.fit_transform(logs)
        self.kmeans.fit(X)
        self.is_fitted = True

    def predict(self, logs: List[str]) -> List[int]:
        if not self.is_fitted:
            # Fallback if not enough data to train
            return [-1] * len(logs)
        X = self.vectorizer.transform(logs)
        return self.kmeans.predict(X).tolist()

    def get_cluster_terms(self, top_n=3) -> Dict[int, List[str]]:
        if not self.is_fitted:
            return {}
        
        terms = self.vectorizer.get_feature_names_out()
        ordered_centroids = self.kmeans.cluster_centers_.argsort()[:, ::-1]
        
        cluster_terms = {}
        for i in range(self.kmeans.n_clusters):
            top_terms = [terms[ind] for ind in ordered_centroids[i, :top_n]]
            cluster_terms[i] = top_terms
            
        return cluster_terms

def analyze_log_patterns(log_entries: List[LogEntry]) -> Dict:
    """
    Groups logs by cluster and identifies frequent patterns.
    """
    raw_messages = [log.message for log in log_entries]
    if not raw_messages:
        return {"clusters": {}, "anomalies": []}

    # Dynamic cluster size: cannot have more clusters than samples
    # For very small batches (e.g. 1 log), we just want to process it, not really "cluster" it effectively
    n_clusters = min(3, len(raw_messages)) 
    if n_clusters < 1:
        n_clusters = 1
        
    clusterer = LogClusterer(n_clusters=n_clusters)
    clusterer.train(raw_messages)
    labels = clusterer.predict(raw_messages)
    
    # Group logs by cluster
    clustered_logs = {}
    for i, label in enumerate(labels):
        if label not in clustered_logs:
            clustered_logs[label] = []
        clustered_logs[label].append(log_entries[i])

    # Infer semantics for each cluster
    cluster_terms = clusterer.get_cluster_terms()
    
    summary = {}
    for label, logs in clustered_logs.items():
        terms = cluster_terms.get(label, [])
        summary[f"cluster_{label}"] = {
            "keywords": terms,
            "count": len(logs),
            "sample": logs[0].message
        }

    return summary
