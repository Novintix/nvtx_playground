CLASSIFY_RESUME_PROMPT = """
You are an expert HR resume classifier.

Task:
Classify the resume into EXACTLY ONE category:

- TECHNICAL → software development, AI/ML, Data Science, Engineering, Programming, Cloud (AWS/Azure),
  Python, PyTorch, TensorFlow, LangChain, FastAPI, Django, etc.

- HR → Human Resources, People & Culture, Talent Acquisition, Recruitment, Learning & Development,
  Organization Development (OD), Organizational Change Management (OCM), Payroll, Onboarding, Employee Engagement.

Rules:
- If the role is OD / OCM / People & Culture → always HR
- If the role is coding / building software / AI/ML engineering → TECHNICAL
- Check job title + most recent role + responsibilities
- Be strict: choose only one

Return ONLY valid JSON (no markdown, no extra text):

{
  "category": "TECHNICAL" or "HR",
  "confidence": 0.95,
  "reason": "short 1 sentence explanation"
}

Resume text:
---
{resume_text}
---
"""
