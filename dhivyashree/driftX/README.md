# DRIFT-X ⚡

**Discussion-Driven Requirement Integrity Tracker**
Detecting Requirement Drift in Real-Time Group Discussions and Codebases using Agentic Reasoning.

---

## 🚀 Project Overview
DRIFT-X is an agentic AI system designed to solve "Silent Requirement Drift". It observes group discussions, understands them, and compares the consensus against the original requirement documents. If the team prioritizing something that contradicts the requirements (e.g., dropping security for speed), DRIFT-X detects it.

**New in v2.0:** It now also analyzes your **Source Code** (via GitHub) to check if the implementation matches both the requirements and the team's decisions.

## 🛠️ Technology Stack

### Core AI & Logic
-   **Python 3.11+**: The core programming language.
-   **LangChain & LangGraph**: Orchestrates the multi-agent workflow (StateGraph).
-   **Google Gemini (`gemini-2.5-flash`)**: The reasoning engine for all agents.
-   **Pydantic**: Ensures strict, validated JSON outputs for reliable analysis.

### RAG & Data Retrieval
-   **LangChain HuggingFace**: Uses local embeddings (`all-MiniLM-L6-v2`) for cost-effective, private vector search.
-   **FAISS**: Fast AI Similarity Search for efficient retrieval of requirement context.
-   **PyGithub**: Fetches repository structure and file contents for code compliance checks.

### User Interface
-   **Streamlit**: The web framework for the interactive Dashboard.
-   **Custom CSS / Glassmorphism**: "Dark Modern" aesthetic with neon accents and frosted glass effects.
-   **Real-time Fragments**: Uses `st.fragment` for high-frequency polling (1s) to simulate real-time chat.

### Backend & Persistence
-   **MongoDB (via `pymongo`)**: Real-time persistence for chat rooms, messages, and state.
-   **Dotenv**: Environment configuration management.

---

## 🧠 How It Works (Architecture)

### 1. Real-Time Chat System
-   Users create/join rooms (stored in MongoDB).
-   Messages are synced in real-time between users.

### 2. The Agentic Pipeline
When "Analyze" is clicked, a **LangGraph** workflow triggers a 4-step process:

1.  **Discussion Focus Agent**: Summarizes the chat, finding key decisions and deprioritized items.
2.  **Requirement Intent Agent**: Extracts goals and hard constraints from the uploaded PDF/TXT.
3.  **Drift Analyzer Agent (with RAG)**:
    -   Uses **FAISS** to retrieve specific requirement sections relevant to the chat topics.
    -   Compares Chat Consensus vs. Requirements.
    -   Outputs a Drift Verdict with evidence.
4.  **Code Compliance Agent**:
    -   Connects to a **GitHub Repository**.
    -   Scans the file structure and key code files.
    -   Verifies if the actual code matches the Requirements and Chat Decisions.

---

## 📦 Setup & Installation

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configuration (`.env`):**
    ```properties
    GOOGLE_API_KEY=AIzaSy...
    MONGO_URI=mongodb://localhost:27017/
    GITHUB_TOKEN=ghp_...  # Required for Code Analysis
    ```

3.  **Run the App:**
    ```bash
    streamlit run app.py
    ```
