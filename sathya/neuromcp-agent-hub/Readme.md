# NeuroMCP Agent Hub 🤖

**Enterprise AI Agent Platform with Multi-Tool Integration**

NeuroMCP Agent Hub is a powerful AI agent platform designed to orchestrate complex workflows across multiple services. It features a sophisticated agentic architecture capable of planning, validating, and executing tasks using integrations with Google Calendar, Slack, and more.

## ✨ Key Features

- **🤖 Autonomous Agents**:
  - **Planner**: Decomposes user requests into executable steps with robust date/time parsing.
  - **Validator**: Ensures data integrity and security before execution.
  - **Executor**: Orchestrates tool calls safely and efficiently.

- **🔌 Seamless Integrations**:
  - **Google Calendar**: Create, manage, and query events.
  - **Slack**: Read messages, post updates, and summarize channel activity using AI.

- **🛡️ Enterprise-Grade Guardrails**:
  - Rate limiting to prevent abuse.
  - Comprehensive data validation.
  - Security gates for high-risk actions (e.g., external API writes).

- **💻 Modern UI**:
  - Built with [Streamlit](https://streamlit.io/) for a responsive, interactive experience.
  - Real-time execution traces and status updates.

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **Google Cloud Console Project** (for Calendar API)
- **Slack App** (for Slack API)
- **Groq API Key** (or compatible OpenAI-style LLM provider)

### 1. Installation

Clone the repository and install dependencies:

```bash
# Clone the repository
git clone <repository_url>
cd neuromcp-agent-hub

# Create virtual environment (optional but recommended)
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the root directory with the following variables:

```ini
# App Configuration
APP_BASE_URL=http://localhost:8000

# LLM Provider (Groq)
GROQ_API_KEY=your_groq_api_key

# Google Calendar Integration
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Slack Integration
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
```

### 3. Running the Application

The application consists of a FastAPI backend and a Streamlit frontend. You need to run both.

**Step 1: Start the Backend Server**

```bash
python start_backend.py
```
*The server will start at `http://localhost:8000`.*

**Step 2: Start the Streamlit UI**

Open a new terminal and run:

```bash
streamlit run streamlit_app.py
```
*The UI will open automatically in your browser (usually `http://localhost:8501`).*

## 📖 Usage Guide

1.  **Connect Services**: Use the sidebar in the UI to authenticate with Google Calendar and Slack.
2.  **Submit Requests**: Type natural language commands in the chat interface.
    - *Example*: "Schedule a team sync with sathya@company.com next Tuesday at 10am and post a notification in #general."
    - *Example*: "Summarize the last 20 messages in #alerts."
3.  **Monitor Execution**: Watch the live execution logs as the agents plan, validate, and execute your request.
4.  **View Results**: See created calendar events and posted messages directly in the results view.

## 🏗️ Project Structure

- `app/`: Core application logic.
  - `agents/`: Agent implementations (Planner, Validator, Executor).
  - `routes/`: API endpoints (Agent runs, OAuth execution).
  - `services/`: Service integrations (Google, Slack, MCP Client).
  - `utils/`: Helper utilities.
- `streamlit_app.py`: Frontend user interface.
- `start_backend.py`: Utility script to launch the API server.
- `test_*.py`: Unit and integration tests for various modules.

## 🧪 Testing

To run the test suite:

```bash
# Run backend tests
python test_backend.py

# Run guardrails validation tests
python test_validation_guardrails.py
```

---
Built with ❤️ by the NeuroMCP Team.
