# Advanced Patient Triage (Multi-Agent Backend)

A safety-first, multi-agent clinical triage backend (NOT a doctor).
This system collects symptom intake, asks follow-up questions, generates a risk hypothesis, applies deterministic safety scoring, routes to the right specialty, and optionally produces a clinician-ready escalation packet.

## Agents
1. **Agent 1 - Symptom Interpretation (LLM)**
   - Extracts normalized symptoms
   - Asks follow-up questions (answer_key-based)
   - Builds clinical notes
   - Stops looping via max rounds + follow-up policy

2. **Agent 2 - Risk Hypothesis (LLM)**
   - Produces triage risk level + care setting
   - Safety-first rules (no diagnosis, no meds)

3. **Agent 3 - Risk Scoring & Safety (Deterministic)**
   - Config-driven rules engine (YAML)
   - Outputs numeric risk score (0..1) + risk level LOW/MEDIUM/HIGH
   - Adds safety flags

4. **Agent 4 - Specialist Routing (LLM)**
   - Routes based on risk + symptoms + safety flags
   - Outputs specialty and recommended care setting

5. **Agent 5 - Human Escalation (LLM, conditional)**
   - Runs only if HIGH risk or requires_immediate_attention flag
   - Produces clinician escalation packet + SBAR summary

---

##  Tech Stack
- FastAPI
- MongoDB (session + history, TTL cleanup)
- Groq LLM (Agent 1/2/4/5)
- Deterministic YAML rules (Agent 3)
- Encryption for stored notes

---

## Setup

### 1) Create virtual env + install dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

### 2)From project root:

python -m uvicorn app.main:app --reload


Server runs at:

✅ http://127.0.0.1:8000