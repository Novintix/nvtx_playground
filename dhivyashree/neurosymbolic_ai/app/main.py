from fastapi import FastAPI, HTTPException
from app.models import AnalysisRequest, RootCause
from app.neural import analyze_log_patterns
from app.symbolic import SymbolicReasoningEngine

app = FastAPI(title="Neuro-Symbolic Incident Analyzer")

symbolic_engine = SymbolicReasoningEngine()

@app.post("/analyze", response_model=dict)
async def analyze_incident(papyload: AnalysisRequest):
    """
    Analyzes logs and alerts to determine root cause.
    """
    try:
        # 1. Symbolic Reasoning (Exact Causality)
        root_cause = symbolic_engine.find_root_cause(papyload.logs, papyload.alerts)
        
        if root_cause:
            return {
                "status": "Root Cause Found",
                "method": "Symbolic Logic",
                "result": root_cause.dict()
            }
            
        # 2. Neural Reasoning (Pattern/Clustering Fallback)
        # If no deterministic rule matches, use ML to cluster logs and give context
        clusters = analyze_log_patterns(papyload.logs)
        
        return {
            "status": "No Definite Root Cause Found (See Patterns)",
            "method": "Neural Clustering",
            "result": {
                "insight": "Symbolic rules did not trigger. Review the following log clusters for anomalies.",
                "clusters": clusters
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def home():
    return {"message": "AI Incident Analyzer Ready. Use POST /analyze"}
