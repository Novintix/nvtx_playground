import os
from typing import TypedDict, Annotated
import asyncio
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import MemorySaver

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

# MCP client configuration for sub-agents
notion_client = MultiServerMCPClient(
    {
        "notion": {
            "transport": "streamable_http",
            "url": "http://127.0.0.1:8001/mcp"
        }
    }
)
filesystem_client = MultiServerMCPClient(
    {
        "filesystem": {
            "transport": "streamable_http",
            "url": "http://127.0.0.1:8002/mcp"
        }
    }
)

async def tools_fs():
    tools = await filesystem_client.get_tools()
    print(tools)

asyncio.run(tools_fs())
# ============================================================================
# Step 1: Create specialized sub-agents
# ============================================================================

async def create_notion_agent():
    """Create the Notion sub-agent with access to Notion MCP tools"""
    tool = await notion_client.get_tools()    
    NOTION_AGENT_PROMPT = """You are a Notion assistant specializing in Notion operations.
You can search Notion pages, retrieve page content, create pages, and manage Notion databases.

When asked to get content from Notion:
1. Search for relevant pages using search tools
2. Retrieve the full content
3. Return the content in a clear, structured format

Always confirm what action you took and what content you retrieved."""
    
    notion_agent = create_agent(
        llm,
        tools=tool,
        system_prompt=NOTION_AGENT_PROMPT
    )
    
    return notion_agent


async def create_filesystem_agent():
    """Create the Filesystem sub-agent with access to Filesystem MCP tools"""
    tool = await filesystem_client.get_tools()
    FILESYSTEM_AGENT_PROMPT = """You are a filesystem assistant specializing in file operations.
You can read files, write files, list directories, and manage the local filesystem.

When asked to save content to a file:
1. Determine the appropriate file path and name
2. Write the content to the file
3. Confirm the file was created with the full path

When asked to read files:
1. Locate the file
2. Read and return its contents

Always confirm what filesystem operation you performed."""
    
    filesystem_agent = create_agent(
        llm,
        tools=tool,
        system_prompt=FILESYSTEM_AGENT_PROMPT
    )
    
    return filesystem_agent


# ============================================================================
# Step 2: Wrap sub-agents as tools for the supervisor
# ============================================================================

# Global variables to store agents (initialized in build_system)
_notion_agent = None
_filesystem_agent = None


@tool
async def manage_notion(request: str) -> str:
    """Interact with Notion to search pages, retrieve content, or manage databases.
    
    Use this when the user wants to:
    - Search for Notion pages
    - Get content from Notion
    - Create or update Notion pages
    - Query Notion databases
    
    Input: Natural language request describing the Notion operation
    Example: "search for git interview notes" or "get the content from the project planning page"
    """
    if _notion_agent is None:
        return "Error: Notion agent not initialized"
    
    print("\n🔵 [NOTION AGENT] Processing request...")
    print(f"   Request: {request}\n")
    
    result = await _notion_agent.ainvoke({
        "messages": [HumanMessage(content=request)]
    })
    
    final_message = result["messages"][-1].content
    print(f"🔵 [NOTION AGENT] Completed\n")
    
    return final_message


@tool
async def manage_filesystem(request: str) -> str:
    """Perform filesystem operations like reading, writing, or listing files.
    
    Use this when the user wants to:
    - Save content to a file
    - Read content from a file
    - List files in a directory
    - Create or delete files
    
    Input: Natural language request describing the file operation
    Example: "save this content to git_notes.txt" or "read the contents of README.md"
    """
    if _filesystem_agent is None:
        return "Error: Filesystem agent not initialized"
    
    print("\n🟢 [FILESYSTEM AGENT] Processing request...")
    print(f"   Request: {request}\n")
    
    result = await _filesystem_agent.ainvoke({
        "messages": [HumanMessage(content=request)]
    })
    
    final_message = result["messages"][-1].content
    print(f"🟢 [FILESYSTEM AGENT] Completed\n")
    
    return final_message


# ============================================================================
# Step 3: Create the supervisor agent
# ============================================================================

async def create_supervisor_agent():
    """Create the supervisor agent that coordinates sub-agents"""
    
    SUPERVISOR_PROMPT = """You are a helpful personal assistant that coordinates specialized agents.

You can:
- Interact with Notion (search pages, get content, manage databases)
- Manage files (read, write, list directories)

When given a complex request:
1. Break it down into steps
2. Call the appropriate specialized agents in sequence
3. Coordinate the results
4. Provide a clear summary to the user

For example, if asked to "get content from Notion and save it to a file":
1. First use manage_notion to retrieve the content
2. Then use manage_filesystem to save it to a file
3. Confirm both actions were completed successfully

Always explain what you're doing at each step."""
    
    supervisor_tools = [manage_notion, manage_filesystem]
    
    supervisor_agent = create_agent(
        llm,
        tools=supervisor_tools,
        system_prompt=SUPERVISOR_PROMPT
    )
    
    return supervisor_agent


# ============================================================================
# Step 4: Build the complete system
# ============================================================================

async def build_system():
    """Initialize all agents and build the system"""
    global _notion_agent, _filesystem_agent
    
    print("🚀 Initializing multi-agent system...")
    print("   - Creating Notion agent...")
    _notion_agent = await create_notion_agent()
    
    print("   - Creating Filesystem agent...")
    _filesystem_agent = await create_filesystem_agent()
    
    print("   - Creating Supervisor agent...")
    supervisor = await create_supervisor_agent()
    
    print("✅ System ready!\n")
    
    return supervisor

# ============================================================================
# Step 5: Main execution
# ============================================================================

async def main():
    """Main execution loop"""
    
    # Build the system
    supervisor = await build_system()
    
    print("Type 'exit', 'quit', or 'bye' to end the conversation.\n")
    print("="*60 + "\n")
    
    exit_words = {"bye", "exit", "quit"}
    
    while True:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() in exit_words:
            print("\n👋 Assistant: Goodbye! Have a great day!")
            break
        
        print("\n" + "="*60)
        print("🤖 SUPERVISOR: Processing your request...")
        print("="*60)
        
        try:
            # Invoke the supervisor agent
            result = await supervisor.ainvoke({
                "messages": [HumanMessage(content=user_input)]
            })
            
            # Get the final response
            final_response = result["messages"][-1].content
            
            print("\n" + "="*60)
            print("📋 FINAL RESPONSE")
            print("="*60)
            print(f"\n{final_response}\n")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")
            print("Please try again or type 'exit' to quit.\n")


if __name__ == "__main__":
    asyncio.run(main())