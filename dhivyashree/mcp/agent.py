import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, HumanMessage

from state import AgentState
from tools import list_github_repos, get_github_commits, get_task_logs

# Initialize LLM with Groq
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


# Define Tools
tools = [list_github_repos, get_github_commits, get_task_logs]
tool_node = ToolNode(tools)

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools)

def agent_node(state: AgentState):
    """The main reasoning node that decides tools to call."""
    messages = state["messages"]
    # If no system message, add one (simplified logic)
    if not messages or not isinstance(messages[0], SystemMessage):
        sys_msg = SystemMessage(content="""You are a context-aware task execution agent. 
Your goal is to gather work context from GitHub to generate a structured End-of-Day (EOD) update for a SPECIFIC repository.

Workflow:
1. Identify the repository the user is interested in.
2. If the user provides a username but no repo, use `list_github_repos` to see available repos.
3. **STOP and Ask** the user which repository to check ("Which one would you like the EOD for?").
4. Once the user selects a repo, use `get_github_commits` to fetch recent commits.
5. Generate the EOD update based SOLELY on the fetched commits.

CRITICAL INSTRUCTIONS:
- Do NOT include "simulated" or "mock" data.
- Do NOT invent "Tasks Completed" if they are not in the commit logs.
- The "EOD Update" must be a summary of the ACTUAL commits found.
- If you have just listed repos, DO NOT generate an EOD yet. Ask the user to choose.
""")
        messages = [sys_msg] + messages
    
    result = llm_with_tools.invoke(messages)
    return {"messages": [result], "reasoning": result.content}

def should_continue(state: AgentState):
    """Decides whether to continue to tools, generate EOD, or stop for user input."""
    messages = state["messages"]
    last_message = messages[-1]
    

    # If the agent wants to call a tool, let it.
    # BUT, we need a guard rail for the 8b model.
    # If the *previous* message was a ToolResult from "list_github_repos", we MUST STOP.
    # We do not want the agent to auto-select a repo immediately.
    
    if last_message.tool_calls:
        # Check history: did we just list repos?
        if len(messages) >= 2:
            prev_msg = messages[-2]
            if prev_msg.type == "tool":
                # Check if it was list_github_repos output
                # The output usually contains "Repositories for" or "Top 10"
                content = str(prev_msg.content)
                if "Repositories for" in content:
                    # Force stop! The agent is trying to proceed too fast.
                    return END
        
        return "tools"
    
    # Check if we have actually fetched commits yet in this conversation
    # We look for a ToolMessage that came from 'get_github_commits'
    for msg in reversed(messages):
         if msg.type == "tool" and "Recent Commits for" in str(msg.content):
             return "eod_generator"

    # If we haven't fetched commits, and aren't calling a tool, we are probably asking the user a question.
    return END

    # If we haven't fetched commits, and aren't calling a tool, we are probably asking the user a question.
    return END

def eod_generator_node(state: AgentState):
    """Generates the final EOD update based on gathered context."""
    # This node runs after the agent has decided it has enough info (no more tool calls)
    messages = state["messages"]
    prompt = HumanMessage(content="""Based on the gathered GitHub commits, generate a structured End-of-Day (EOD) update for the repository.
    
Format:
## EOD Update for [Repository Name]

### 🚀 Key Activity
[Summary of the main work done based on commit messages]

### 📝 Commits
[List of commits with Author and Date]

(Do NOT include any generic "Simulated" sections or "Task Logs" if they were not fetched.)
""")
    
    # We use the raw LLM (without tools forced, or just plain invoke)
    # Ideally reuse context. 
    response = llm.invoke(messages + [prompt])
    
    content = response.content
    if isinstance(content, list):
        # Handle case where content is a list of parts (e.g. [{'type': 'text', 'text': '...'}])
        text_parts = []
        for part in content:
            if isinstance(part, dict) and "text" in part:
                text_parts.append(part["text"])
            elif isinstance(part, str):
                text_parts.append(part)
        content = "\n".join(text_parts)
        
    return {"eod_update": content, "messages": [response]}

# Build the Graph
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.add_node("eod_generator", eod_generator_node)

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        "eod_generator": "eod_generator",
        END: END
    }
)

workflow.add_edge("tools", "agent")
workflow.add_edge("eod_generator", END)

# Compile functions will happen in main.py where we inject the checkpointer
