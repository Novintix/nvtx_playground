# DecodX — Secure Decision Intelligence

DecodX is a next-generation decision intelligence platform designed to bridge the gap between corporate financial data and policy governance. By leveraging the **Model Context Protocol (MCP)** and **LangGraph**, DecodX provides a secure, role-aware environment where analysts and executives can interact with sensitive data under the protection of automated governance guardrails.

## 🚀 The Mission

In modern enterprises, data is often siloed, and policy compliance is a manual, error-prone process. DecodX solves this by:
- **Governing AI Reasoning**: Every query and agent action is audited and authorized against corporate roles.
- **Grounding and Context**: Using secure RAG to ensure decisions are based on verified financial records and latest policies.
- **Interactive Compliance**: Moving beyond passive alerts to "Compliance Handshakes"—where the system negotiates policy changes with human oversight.

## 🛠️ Technology Stack

- **Core Intelligence**: LangGraph (Orchestration) & MCP (Tooling & Security)
- **Frontend**: Streamlit (Reactive UI)
- **Backend**: Python-based MCP Server (SSE)
- **Data Layers**: ChromaDB (Vector Search) & Pandas (Financial Analysis)

## 👤 User Personas & Permissions

DecodX implements a strict **Role-Based Access Control (RBAC)** system at the tool level:

| Role | Financial Access | Policy Modification | Analytics Dashboard |
| :--- | :--- | :--- | :--- |
| **Guest** | 🚫 Locked | 🚫 Blocked | 🚫 Restricted |
| **Analyst** | ✅ Full Access | ⚠️ Proposed Only | ✅ Full View |
| **Admin** | ✅ Full Access | ✅ Full Authority | ✅ Full View |

## 📦 Getting Started

### 1. Prerequisite Setup
Ensure you have a `.env` file configured in the root directory and a virtual environment activated.

```bash
# Activate virtual environment
source .venv/bin/activate
```

### 2. Launch the Backend (MCP Server)
The backend manages the secure tools and governance logic.
```bash
python3 backend/main.py
```

### 3. Launch the Frontend
The frontend provides the interactive chat and dashboard experience.
```bash
streamlit run src/main.py
```

## 🛡️ Governance Features

### Compliance Handshake
When an Analyst proposes a policy change, DecodX enters a "Handshake" state. It identifies **Hurdles & Risks**—contradictions between the proposal and existing rules—and holds the update until an Admin provides final confirmation.

### Secure Audit Logs
Every interaction in DecodX is logged to `mcp_audit.log`, capturing entry/exit points, authorization results, and data retrieval events to ensure a tamper-proof audit trail.