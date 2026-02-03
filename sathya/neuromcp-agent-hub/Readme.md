# 🤖 NeuroMCP Agent Hub

**Enterprise AI Agent Platform with Multi-Tool Integration**

A production-ready, multi-agent system that orchestrates complex workflows across Google Calendar and Slack using LangGraph, Groq LLM, and intelligent guardrails.

---

## 🌟 Features

### Core Capabilities
- **Multi-Agent Architecture**: Specialized agents for planning, validation, execution, and reporting
- **LLM-Powered Request Filtering**: Intelligent scope validation to reject inappropriate queries
- **Real-time Tool Integration**: Direct Google Calendar and Slack API integration
- **Robust Guardrails**: 
  - Data validation (emails, dates, attendees)
  - Rate limiting to prevent abuse
  - Pre-execution validation with instant feedback
- **OAuth 2.0 Authentication**: Secure token management with auto-refresh
- **Beautiful UI**: Premium Streamlit interface with modern design

### Intelligent Validation
- **Email validation** with format checking
- **DateTime validation** (prevents past dates, validates ranges)
- **Attendee validation** (duplicate detection, count limits)
- **Slack channel validation** (format rules, character limits)
- **Sensitive data detection** (API keys, passwords, credit cards)
- **Rate limiting** (per-tool and global request throttling)

---
<img width="1535" height="742" alt="diagram-export-3-2-2026-11_43_26-pm" src="https://github.com/user-attachments/assets/867543a3-27c7-4357-8d46-014da91436a0" />

## 📁 Project Structure

This project follows a clean, production-level architecture:

```
neuromcp-agent-hub/
├── app/
│   ├── agents/                 # Multi-agent system
│   │   ├── planner/           # 🧠 The Architect: Creates execution plans
│   │   ├── validator/         # 🛡️ The Safety Officer: Validates plans & guardrails
│   │   ├── executor/          # ⚡ The Action Hero: Executes approved steps
│   │   ├── tool_discovery/    # 🧰 The Gadget Scout: Discovers available tools
│   │   └── report/            # 📊 The Reporter: Generates final reports
│   │
│   ├── services/
│   │   ├── oauth/             # 🔐 OAuth Authentication & Token Management
│   │   ├── tools/             # 🛠️ Real Google Calendar & Slack Implementations
│   │   ├── mcp/               # 🔌 MCP Client (Optional)
│   │   └── ai/                # 🤖 AI Services (Summarization)
│   │
│   ├── routes/                # FastAPI endpoints for agents, OAuth, etc.
│   ├── langgraph/             # LangGraph workflow orchestration
│   └── config/                # Configuration settings
│
├── streamlit_app.py           # Frontend UI
├── start_backend.py           # Backend server
├── requirements.txt           # Dependencies
├── .env                       # Environment variables
└── .tokens.json               # Secure token storage
```

### Key Design Principles

1. **No Test Files in Root**: All test files removed for production. Testing is done through the UI.
2. **No Mock Data**: Uses **real APIs** (Google Calendar, Slack) and production storage.
3. **Separation of Concerns**: Clear split between Agents (logic), Services (integrations), and Routes (API).
4. **Security First**: Secrets in `.env`, tokens in `.tokens.json`, sensitive files git-ignored.
5. **Production-Ready**: Comprehensive error handling, auto-refresh tokens, and rate limiting.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Cloud Project (for Calendar API)
- Slack Workspace (for Slack API)
- Groq API Key (for LLM)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd neuromcp-agent-hub
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Create a `.env` file:
```env
# Groq LLM
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant

# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Slack OAuth
SLACK_CLIENT_ID=your_slack_client_id
SLACK_CLIENT_SECRET=your_slack_client_secret
SLACK_REDIRECT_URI=http://localhost:8000/auth/slack/callback

# Server
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:8501
```

4. **Run the application**

Terminal 1 - Backend:
```bash
python start_backend.py
```

Terminal 2 - Frontend:
```bash
streamlit run streamlit_app.py
```

5. **Access the app**
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000

---

## 🔐 OAuth Setup

### Google Calendar

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/auth/google/callback`
6. Copy Client ID and Secret to `.env`

### Slack

1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app
3. Add OAuth scopes: `channels:read`, `channels:history`, `chat:write`
4. Add redirect URI: `http://localhost:8000/auth/slack/callback`
5. Copy Client ID and Secret to `.env`

---

## 💡 Usage Examples

### Create a Calendar Event
```
"Create a team meeting on Feb 5 at 6pm with sathya@company.com"
```

### Post to Slack
```
"Send 'Hi team, meeting in 5 minutes!' to #general"
```

### List Events
```
"Show me my upcoming meetings"
```

### Summarize Slack
```
"Summarize the #team-chat conversations"
```

---

## 🛡️ Guardrails & Validation

The system includes multiple layers of protection:

1. **Pre-Validation** (Before Planning)
   - LLM-powered request scope filtering
   - Rejects knowledge questions, greetings, out-of-scope requests (e.g., "who is X")

2. **Plan Validation** (After Planning)
   - Tool schema & dependency validation
   - Data validation (dates, emails, formats)
   - Sensitive data detection

3. **Execution Validation**
   - Approval gates for high-risk tools
   - Token refresh handling & error recovery

---

## 🏗️ Architecture

### Multi-Agent Workflow

```
User Request
    ↓
[Pre-Validator] → Rejects invalid/out-of-scope requests
    ↓
[Tool Discovery] → Finds available tools
    ↓
[Planner] → Creates execution plan (LLM)
    ↓
[Validator] → Validates plan + data
    ↓
[Executor] → Executes approved steps
    ↓
[Report] → Generates final report
    ↓
User sees results
```

### Key Technologies
- **LangGraph**: Workflow orchestration
- **Groq**: Fast LLM inference (Llama 3.1)
- **FastAPI**: Backend API
- **Streamlit**: Frontend UI
- **httpx**: Async HTTP client
- **Pydantic**: Data validation

---

## 📊 Rate Limiting

Default limits (configurable in `app/agents/validator/rate_limiter.py`):

- **Overall requests**: 10 per minute
- **Calendar operations**: 5 per minute
- **Slack messages**: 5 per minute

---

## 🔧 Configuration

### Timezone
Default timezone is `Asia/Kolkata`. Change in:
- `app/agents/planner/agent.py` → `DEFAULT_TZ`

### LLM Model
Change in `.env`:
```env
GROQ_MODEL=llama-3.1-70b-versatile  # For better quality
```

---

## 🐛 Troubleshooting

### "Google Calendar not connected"
- Click "Connect" button in sidebar
- Authorize the app
- Check `.tokens.json` file exists

### "Rate limit exceeded"
- Wait 60 seconds
- Or adjust limits in `rate_limiter.py`

### "Invalid datetime format"
- Use ISO format: `2026-02-05T18:00:00+05:30`
- Include timezone offset

---

## 📝 License

MIT License - feel free to use for your projects!

---

## 👨‍💻 Author

**Sathya**  
Built with ❤️ using LangGraph, Groq, and modern AI technologies

---

## 🙏 Acknowledgments

- Groq for fast LLM inference
- Google Calendar API
- Slack API
- LangChain/LangGraph community
